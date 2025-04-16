/*#[derive(Debug, serde::Serialize, serde::Deserialize)]
enum FunctionalType {
    M062X,
}

#[allow(non_camel_case_types)]
#[derive(Debug, serde::Serialize, serde::Deserialize)]
enum BasisType {
    _6_31pG_D,
    def2SVP,
}

#[derive(Debug, serde::Serialize, serde::Deserialize)]
struct QuantumMechanicsType {
    functional_type: FunctionalType,
    basis_type: BasisType,
}
*/

// manual backfilling:
// SELECT MIN(local_path + 1) FROM runs WHERE (local_path + 1) NOT IN (SELECT local_path FROM runs);
// SELECT * FROM molecules WHERE compound_id NOT IN (SELECT compound_id FROM runs) ORDER BY rotatable_bonds ASC, num_atoms ASC LIMIT 5;

// Deleting entries
// DELETE FROM runs WHERE local_path=-1;

#[derive(Debug, serde::Serialize, serde::Deserialize)]
struct Molecule {
    compound_id: String,
    smiles: String,
    iupac: String,
    experimental_value: f64,
    experimental_uncertainty: f64,
    calculated_value: f64,
    calculated_uncertainty: f64,
    experimental_reference: String,
    calculated_reference: String,
    notes: Option<String>,
    rotatable_bonds: u16,
    num_atoms: u16,
}

#[derive(Debug, PartialEq, serde::Serialize, serde::Deserialize)]
enum StatusType {
    Planned,
    Running,
    Received,
    Finished,
    Failed,
}

#[allow(non_camel_case_types)]
#[derive(Debug, PartialEq, serde::Serialize, serde::Deserialize)]
enum RemoteHostType {
    localhost,
    katana,
    katana2,
    gadi,
    setonix,
}

impl RemoteHostType {
    fn get_data_host(&self) -> &str {
        match self {
            RemoteHostType::localhost => "localhost",
            RemoteHostType::katana => "kdm",
            RemoteHostType::katana2 => "kdm2",
            RemoteHostType::gadi => "gadi-dm",
            RemoteHostType::setonix => "setonix-data",
        }
    }
}

#[derive(Debug, PartialEq, serde::Serialize, serde::Deserialize)]
enum RunResourceType {
    Cpu,
    Gpu,
}

#[allow(clippy::upper_case_acronyms)]
#[derive(Debug, PartialEq, serde::Serialize, serde::Deserialize)]
enum RunType {
    RelaxedMinEquilGAFF,
    RelaxedForwardGAFF,
    RelaxedReversedGAFF,
    RelaxedBarGAFF,
    FrozenMinEquilCENSO,
    FrozenMinEquilCENSO3,
    FrozenForwardCENSO,
    FrozenForwardCENSO3,
    FrozenForwardCENSO50,
    FrozenForwardCENSO51,
    FrozenReversedCENSO,
    FrozenReversedCENSO3,
    FrozenReversedCENSO50,
    FrozenReversedCENSO51,
    FrozenBarCENSO,
    FrozenBarCENSO3,
    FrozenBarCENSO5,
    CREST,
    CENSO,
    VacuumCREST,
    VacuumCENSO,
    ORCA,
    ORCAr2SCAN3c,
}

impl RunType {
    fn get_resource_type(&self) -> RunResourceType {
        match self {
            RunType::RelaxedForwardGAFF | RunType::RelaxedReversedGAFF => RunResourceType::Gpu,
            _ => RunResourceType::Cpu,
        }
    }
}

#[derive(Debug, serde::Serialize, serde::Deserialize)]
struct Run {
    compound_id: String,
    run_type: RunType,
    status: StatusType,
    local_path: u32,
    remote_host: RemoteHostType,
    remote_path: String,
}

#[allow(non_snake_case)]
#[derive(Debug, serde::Serialize, serde::Deserialize)]
struct KatanaJob {
    Job_Name: u32,
    job_state: char,
}

#[allow(non_snake_case)]
#[derive(Debug, serde::Serialize, serde::Deserialize)]
struct GadiJob {
    Job_Name: String,
    job_state: char,
}

#[derive(Debug, serde::Serialize, serde::Deserialize)]
struct SetonixJob {
    name: String,
    job_state: String,
}

fn update_run_status(
    local_path: u32,
    new_status: StatusType,
    connection: &rusqlite::Connection,
) -> Result<(u32, StatusType), Box<dyn std::error::Error>> {
    connection.execute(
        &format!(
            "UPDATE runs SET status = '{:?}' WHERE local_path = {}",
            new_status, local_path
        ),
        [],
    )?;
    Ok((local_path, new_status))
}

fn receive_files(
    Run {
        compound_id: _,
        run_type: _,
        status,
        local_path,
        remote_host,
        remote_path,
    }: Run,
    connection: &rusqlite::Connection,
) -> Result<(), Box<dyn std::error::Error>> {
    // check if status is correct
    if status != StatusType::Running {
        Err("Invalid status")?;
    }

    run_program(vec![
        "rsync",
        "-rz",
        &format!("{}:{}", remote_host.get_data_host(), remote_path),
        &format!("data/{}", local_path),
    ])?;
    println!(
        "{:?}",
        update_run_status(local_path, StatusType::Received, connection)
    );
    Ok(())
}

fn submit_job(
    Run {
        compound_id: _,
        run_type: _,
        status,
        local_path,
        remote_host,
        remote_path,
    }: &Run,
) -> Result<(), Box<dyn std::error::Error>> {
    println!(
        "submit job {}, {:?}, {}",
        local_path, remote_host, remote_path
    );

    if status != &StatusType::Planned {
        println!("invalid status {:?}", status);
        Err("Invalid status")?
    }

    match remote_host {
        RemoteHostType::localhost => Err("invalid target localhost")?,
        RemoteHostType::setonix => run_program(vec![
            "ssh",
            &format!("{:?}", remote_host),
            &format!("cd {}; sbatch {}", remote_path, local_path),
        ]),
        RemoteHostType::katana | RemoteHostType::katana2 | RemoteHostType::gadi => {
            run_program(vec![
                "ssh",
                &format!("{:?}", remote_host),
                &format!("cd {}; qsub {}", remote_path, local_path),
            ])
        }
    }?;

    Ok(())
}

fn copy(source: &str, dest: &str) -> Result<(), Box<dyn std::error::Error>> {
    println!("copying from {} to {}", source, dest);
    std::fs::copy(source, dest)?;
    Ok(())
}

fn create_dir_if(dir: &str) -> Result<(), Box<dyn std::error::Error>> {
    println!("creating directory if not exists {}", dir);
    if !std::path::Path::new(&dir).exists() {
        std::fs::create_dir(dir)?;
    }
    Ok(())
}

fn run_program(args: Vec<&str>) -> Result<(), Box<dyn std::error::Error>> {
    println!("running program with args {:?}", args);
    let mut args = args.into_iter();
    let mut process = std::process::Command::new(args.next().ok_or("No command found")?);
    for arg in args {
        process.arg(arg);
    }
    let output = process.output()?;
    println!("{:#?}", output);
    if output.status.success() {
        Ok(())
    } else {
        Err("program exit unsuccessful")?
    }
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    println!("Loading database");
    let connection = rusqlite::Connection::open("frozen_solute_model_new.db")?;
    let mut statement = connection.prepare("SELECT * FROM molecules")?;
    let molecules = serde_rusqlite::from_rows::<Molecule>(statement.query([])?);
    for molecule in molecules {
        molecule?;
    }

    let mut statement = connection.prepare("SELECT * FROM runs")?;
    let runs = serde_rusqlite::from_rows::<Run>(statement.query([])?);
    for run in runs {
        run?;
    }

    let modified = std::fs::metadata("server/katana.json")?
        .modified()?
        .duration_since(std::time::SystemTime::UNIX_EPOCH)?
        + std::time::Duration::from_secs(30);
    let now = std::time::SystemTime::now().duration_since(std::time::SystemTime::UNIX_EPOCH)?;

    if modified < now {
        println!("File Older than 30 Seconds, Not sleeping")
    } else {
        let sleep = modified - now;
        println!("Sleeping for {:?}", sleep);
        std::thread::sleep(sleep);
    }

    println!("Getting run data");
    let mut jobs: Vec<u32> = vec![];

    // katana
    {
        println!("Updating katana");
        let katana_raw_json = std::fs::File::create("server/katana_raw.json")?;
        let output = std::process::Command::new("ssh")
            .arg("katana2")
            .arg("qstat -f -F json")
            .stdout(katana_raw_json)
            .output();
        assert!(output.is_ok(), "{output:?}");
        assert!(output?.status.success());
        let katana_json = std::fs::File::create("server/katana.json")?;
        let output = std::process::Command::new("jq")
            .arg("[.Jobs | to_entries[] | select(.value.Job_Owner | startswith(\"z5358697\")) | .value]")
            .arg("server/katana_raw.json")
            .stdout(katana_json)
            .output();
        assert!(output.is_ok(), "{output:?}");
        assert!(output?.status.success());
        let katana2_json = std::fs::File::create("server/katana2.json")?;
        let output = std::process::Command::new("jq")
            .arg("[.Jobs | to_entries[] | select(.value.Job_Owner | startswith(\"z5382435\")) | .value]")
            .arg("server/katana_raw.json")
            .stdout(katana2_json)
            .output();
        assert!(output.is_ok(), "{output:?}");
        assert!(output?.status.success());
        let output = std::process::Command::new("rm")
            .arg("server/katana_raw.json")
            .output();
        assert!(output.is_ok(), "{output:?}");
        assert!(output?.status.success());

        jobs.append(
            &mut serde_json::from_str::<Vec<KatanaJob>>(&std::fs::read_to_string(
                "server/katana2.json",
            )?)
                .unwrap_or_default()
                .into_iter()
                .map(|i| i.Job_Name)
                .collect::<Vec<u32>>(),
        );

        jobs.append(
            &mut serde_json::from_str::<Vec<KatanaJob>>(&std::fs::read_to_string(
                "server/katana.json",
            )?)
                .unwrap_or_default()
                .into_iter()
                .map(|i| i.Job_Name)
                .collect::<Vec<u32>>(),
        );
    }

    // gadi
    /* {
        println!("Updating gadi");
        let gadi_raw_json = std::fs::File::create("server/gadi_raw.json")?;
        let output = std::process::Command::new("ssh")
            .arg("gadi")
            .arg("qstat -f -F json")
            .stdout(gadi_raw_json)
            .output();
        assert!(output.is_ok(), "{output:?}");
        assert!(output?.status.success());
        let gadi_json = std::fs::File::create("server/gadi.json")?;
        let output = std::process::Command::new("jq")
            .arg("try([.Jobs | to_entries[] | select(.value.Job_Owner | startswith(\"mw7780\")) | .value]) // []")
            .arg("server/gadi_raw.json")
            .stdout(gadi_json)
            .output();
        assert!(output.is_ok(), "{output:?}");
        assert!(output?.status.success());

        jobs.append(
            &mut serde_json::from_str::<Vec<GadiJob>>(&std::fs::read_to_string(
                "server/gadi.json",
            )?)
                .unwrap_or_default()
                .into_iter()
                .map(|i| i.Job_Name.parse::<u32>().unwrap())
                .collect::<Vec<u32>>(),
        );
    }*/

    // setonix
    {
        println!("Updating setonix");
        let setonix_raw_json = std::fs::File::create("server/setonix_raw.json")?;
        let output = std::process::Command::new("ssh")
            .arg("setonix")
            .arg("squeue --user mwang1 --json")
            .stdout(setonix_raw_json)
            .output();
        assert!(output.is_ok(), "{output:?}");
        assert!(output?.status.success());
        let setonix = std::fs::File::create("server/setonix.json")?;
        let output = std::process::Command::new("jq")
            .arg("[.jobs[] | {name: .name, job_state: .job_state[0]}]")
            .arg("server/setonix_raw.json")
            .stdout(setonix)
            .output();
        assert!(output.is_ok(), "{output:?}");
        assert!(output?.status.success());

        jobs.append(
            &mut serde_json::from_str::<Vec<SetonixJob>>(&std::fs::read_to_string(
                "server/setonix.json",
            )?)
                .unwrap_or_default()
                .into_iter()
                .map(|i| i.name.parse::<u32>().unwrap())
                .collect::<Vec<u32>>(),
        );
    }

    jobs.sort_unstable(); // they are supposed to be unique anyway
    println!("Jobs: {:?}", jobs);

    // get gpu jobs
    let mut statement = connection.prepare("SELECT * FROM runs WHERE run_type = 'RelaxedForwardGAFF' OR run_type = 'RelaxedReversedGAFF'")?;
    let runs = serde_rusqlite::from_rows::<Run>(statement.query([])?);
    let mut gpu_jobs = vec![];
    for run in runs {
        gpu_jobs.push(run?.local_path);
    }

    let mut katana_cpu_queue_length: u8 =
        serde_json::from_str::<Vec<KatanaJob>>(&std::fs::read_to_string("server/katana.json")?)
            .unwrap_or_default()
            .into_iter()
            .fold(0, |acc, x| {
                acc + (x.job_state == 'Q' && !gpu_jobs.contains(&x.Job_Name)) as u8
            });
    let mut katana2_cpu_queue_length: u8 =
        serde_json::from_str::<Vec<KatanaJob>>(&std::fs::read_to_string("server/katana2.json")?)
            .unwrap_or_default()
            .into_iter()
            .fold(0, |acc, x| {
                acc + (x.job_state == 'Q' && !gpu_jobs.contains(&x.Job_Name)) as u8
            });
    let mut katana_gpu_queue_length: u8 =
        serde_json::from_str::<Vec<KatanaJob>>(&std::fs::read_to_string("server/katana.json")?)
            .unwrap_or_default()
            .into_iter()
            .fold(0, |acc, x| {
                acc + (x.job_state == 'Q' && gpu_jobs.contains(&x.Job_Name)) as u8
            });
    let mut katana2_gpu_queue_length: u8 =
        serde_json::from_str::<Vec<KatanaJob>>(&std::fs::read_to_string("server/katana2.json")?)
            .unwrap_or_default()
            .into_iter()
            .fold(0, |acc, x| {
                acc + (x.job_state == 'Q' && gpu_jobs.contains(&x.Job_Name)) as u8
            });
    let mut gadi_queue_length: u8 =
        serde_json::from_str::<Vec<GadiJob>>(&std::fs::read_to_string("server/gadi.json")?)
            .unwrap_or_default()
            .into_iter()
            .fold(0, |acc, x| acc + (x.job_state == 'Q') as u8);
    let mut setonix_queue_length: u8 =
        serde_json::from_str::<Vec<SetonixJob>>(&std::fs::read_to_string("server/setonix.json")?)
            .unwrap_or_default()
            .into_iter()
            .fold(0, |acc, x| acc + (x.job_state == "PENDING") as u8);

    println!("katana cpu queue length: {}", katana_cpu_queue_length);
    println!("katana2 cpu queue length: {}", katana2_cpu_queue_length);
    println!("katana gpu queue length: {}", katana_gpu_queue_length);
    println!("katana2 gpu queue length: {}", katana2_gpu_queue_length);
    println!("gadi queue length: {}", gadi_queue_length);
    println!("setonix queue length: {}", setonix_queue_length);

    let mut planned_cpu: u8 = 0;
    let mut planned_gpu: u8 = 0;
    let mut statement = connection.prepare("SELECT * FROM runs")?;
    let runs = serde_rusqlite::from_rows::<Run>(statement.query([])?);
    for run in runs {
        let run = run?;
        match &run.status {
            StatusType::Planned => 'match_status: {
                match &run.run_type.get_resource_type() {
                    RunResourceType::Cpu => {
                        planned_cpu += 1;
                    }
                    RunResourceType::Gpu => {
                        planned_gpu += 1;
                    }
                }

                if run.remote_host == RemoteHostType::localhost {
                    if ((katana_cpu_queue_length < 5)
                        && ((run.run_type == RunType::FrozenForwardCENSO3)
                        || (run.run_type == RunType::FrozenReversedCENSO3)
                        || (run.run_type == RunType::RelaxedMinEquilGAFF)))
                        || ((katana_cpu_queue_length < 10)
                        && ((run.run_type == RunType::CREST)
                        || (run.run_type == RunType::VacuumCREST)
                        || (run.run_type == RunType::ORCA) || (run.run_type == RunType::ORCAr2SCAN3c)))
                    {
                        let output = connection.execute(
                            &format!(
                                "UPDATE runs SET remote_path = '/srv/scratch/z5358697/.automated/{}/', remote_host = 'katana' WHERE local_path = {}",
                                run.local_path, run.local_path
                            ),
                            [],
                        );
                        println!("pick remote host {:?}", output);
                        katana_cpu_queue_length += 1;
                    } else if ((katana_gpu_queue_length < 5)
                        && ((run.run_type == RunType::RelaxedForwardGAFF)
                        || (run.run_type == RunType::RelaxedReversedGAFF)))
                         || ((katana_cpu_queue_length < 10) && (run.run_type == RunType::ORCA) || (run.run_type == RunType::ORCAr2SCAN3c))
                    {
                        let output = connection.execute(
                            &format!(
                                "UPDATE runs SET remote_path = '/srv/scratch/z5358697/.automated/{}/', remote_host = 'katana' WHERE local_path = {}",
                                run.local_path, run.local_path
                            ),
                            [],
                        );
                        println!("pick remote host {:?}", output);
                        katana_gpu_queue_length += 1;
                    } else if (katana2_gpu_queue_length < 5)
                        && ((run.run_type == RunType::RelaxedForwardGAFF)
                        || (run.run_type == RunType::RelaxedReversedGAFF))
                    {
                        let query = format!(
                            "UPDATE runs SET remote_path = '/srv/scratch/z5382435/.automated/{}/', remote_host = 'katana2' WHERE local_path = {}",
                            run.local_path, run.local_path
                        );
                        connection.execute(&query, [])?;
                        println!("pick remote host {:?}", query);
                        katana2_gpu_queue_length += 1;
                    } else if ((katana2_cpu_queue_length < 5)
                        && ((run.run_type == RunType::FrozenForwardCENSO3)
                        || (run.run_type == RunType::FrozenReversedCENSO3)))
                        || ((katana2_cpu_queue_length < 10)
                        && (run.run_type == RunType::VacuumCREST))
                    {
                        let output = connection.execute(
                            &format!(
                                "UPDATE runs SET remote_path = '/srv/scratch/z5382435/.automated/{}/', remote_host = 'katana2' WHERE local_path = {}",
                                run.local_path, run.local_path
                            ),
                            [],
                        );
                        println!("pick remote host {:?}", output);
                        katana2_cpu_queue_length += 1;
                    } else if (setonix_queue_length < 1)
                        && ((run.run_type == RunType::VacuumCENSO)
                        || (run.run_type == RunType::FrozenForwardCENSO3)
                        || (run.run_type == RunType::FrozenReversedCENSO3))
                    {
                        connection.execute(
                            &format!(
                                "UPDATE runs SET remote_path = '/scratch/pawsey0265/mwang1/.automated/{}/', remote_host = 'setonix' WHERE local_path = {}",
                                run.local_path, run.local_path
                            ),
                            [],
                        )?;
                        setonix_queue_length += 1;
                        println!("pick remote host setonix");
                    } else {
                        println!("all queues busy, skipping");
                    }
                    break 'match_status;
                }

                // create dir
                create_dir_if(&format!("data/{}", run.local_path))?;

                match &run.run_type {
                    RunType::RelaxedMinEquilGAFF => {
                        let output = std::process::Command::new("python")
                            .arg("prep.py")
                            .arg(&run.compound_id)
                            .arg(run.local_path.to_string())
                            .output()?;
                        println!("python prep.py {:?}", output);
                        if !output.status.success() {
                            break 'match_status;
                        }
                    }
                    RunType::RelaxedForwardGAFF | RunType::RelaxedReversedGAFF => {
                        let mut statement = connection.prepare(&format!(
                            "SELECT * FROM runs WHERE compound_id == '{}' AND run_type = 'RelaxedMinEquilGAFF'",
                            run.compound_id,
                        ))?;
                        let min_equil_path = serde_rusqlite::from_rows::<Run>(statement.query([])?)
                            .next()
                            .ok_or("No prep found")??
                            .local_path;

                        for suffix in [".prmtop", ".pdb", "_equil.coor", "_equil.vel", "_equil.xsc"]
                        {
                            let source =
                                format!("data/{}/{}{}", min_equil_path, run.compound_id, suffix);
                            let dest =
                                format!("data/{}/{}{}", run.local_path, run.compound_id, suffix);
                            copy(&source, &dest)?;
                        }

                        copy("fep.tcl", &format!("data/{}/fep.tcl", run.local_path))?;

                        // run prod script
                        match &run.run_type {
                            RunType::RelaxedForwardGAFF => run_program(vec![
                                "python",
                                "prod.forward.py",
                                &run.compound_id,
                                &run.local_path.to_string(),
                            ])?,
                            RunType::RelaxedReversedGAFF => run_program(vec![
                                "python",
                                "prod.reversed.py",
                                &run.compound_id,
                                &run.local_path.to_string(),
                            ])?,
                            _ => panic!(),
                        }
                    }
                    RunType::CREST | RunType::VacuumCREST => {
                        run_program(vec![
                            "python",
                            "mol2-to-xyz.py",
                            &format!("FreeSolv/mol2files_gaff/{}.mol2", run.compound_id),
                            &format!("data/{}/{}.xyz", run.local_path, run.compound_id),
                        ])?;

                        if run.run_type == RunType::CREST {
                            run_program(vec![
                                "python",
                                "crest.py",
                                &format!("data/{}/{}", run.local_path, run.local_path),
                                &run.compound_id,
                            ])?;
                        } else if run.run_type == RunType::VacuumCREST {
                            run_program(vec![
                                "python",
                                "vacuum-crest.py",
                                &format!("data/{}/{}", run.local_path, run.local_path),
                                &run.compound_id,
                            ])?;
                        } else {
                            panic!()
                        }
                    }
                    RunType::CENSO | RunType::VacuumCENSO => {
                        let mut statement = match &run.run_type {
                            RunType::CENSO => connection.prepare(&format!(
                                "SELECT * FROM runs WHERE compound_id == '{}' AND run_type = 'CREST'",
                                run.compound_id,
                            ))?,
                            RunType::VacuumCENSO => connection.prepare(&format!(
                                "SELECT * FROM runs WHERE compound_id == '{}' AND run_type = 'VacuumCREST'",
                                run.compound_id,
                            ))?,
                            run_type => panic!("{:?}", run_type),
                        };
                        let crest_path = serde_rusqlite::from_rows::<Run>(statement.query([])?)
                            .next()
                            .ok_or("No prep found")??
                            .local_path;

                        copy(
                            &format!("data/{}/crest_conformers.xyz", crest_path),
                            &format!("data/{}/crest_conformers.xyz", run.local_path),
                        )?;

                        run_program(vec![
                            "python",
                            "censo.py",
                            &format!("data/{}/{}", run.local_path, run.local_path),
                            &format!("{:?}", run.remote_host),
                        ])?;
                    }
                    RunType::FrozenForwardCENSO3 | RunType::FrozenReversedCENSO3 | RunType::FrozenForwardCENSO50 | RunType::FrozenForwardCENSO51 | RunType::FrozenReversedCENSO50 | RunType::FrozenReversedCENSO51 => {
                        let mut statement = connection.prepare(&format!(
                            "SELECT * FROM runs WHERE compound_id == '{}' AND run_type = 'FrozenMinEquilCENSO3'",
                            run.compound_id,
                        ))?;
                        let min_equil_path = serde_rusqlite::from_rows::<Run>(statement.query([])?)
                            .next()
                            .ok_or("No prep found")??
                            .local_path;

                        for suffix in [".prmtop", ".pdb", "_equil.coor", "_equil.vel", "_equil.xsc"]
                        {
                            let source =
                                format!("data/{}/{}{}", min_equil_path, run.compound_id, suffix);
                            let dest =
                                format!("data/{}/{}{}", run.local_path, run.compound_id, suffix);
                            copy(&source, &dest)?;
                        }

                        copy("fep.tcl", &format!("data/{}/fep.tcl", run.local_path))?;

                        // run prod script
                        run_program(vec![
                            "python",
                            "prod.frozen.py",
                            &run.compound_id,
                            &run.local_path.to_string(),
                            &format!("{:?}", run.remote_host),
                            &format!("{:?}", run.run_type)
                        ])?;
                    }
                    RunType::ORCA | RunType::ORCAr2SCAN3c => {
                        let mut statement = connection.prepare(&format!(
                            "SELECT * FROM runs WHERE compound_id == '{}' AND run_type = 'CENSO'",
                            run.compound_id,
                        ))?;
                        let censo_path = serde_rusqlite::from_rows::<Run>(statement.query([])?)
                            .next()
                            .ok_or("No censo found")??
                            .local_path;

                        copy(
                            &format!("data/{}/2_OPTIMIZATION.xyz", censo_path),
                            &format!("data/{}/censo.xyz", run.local_path),
                        )?;

                        run_program(vec![
                            "python",
                            "trim_xyz.py",
                            &format!("data/{}/censo.xyz", run.local_path),
                        ])?;

                        let mut statement = connection.prepare(&format!(
                            "SELECT * FROM runs WHERE compound_id == '{}' AND run_type = 'VacuumCENSO'",
                            run.compound_id,
                        ))?;
                        let vacuum_censo_path =
                            serde_rusqlite::from_rows::<Run>(statement.query([])?)
                                .next()
                                .ok_or("No vacuum censo found")??
                                .local_path;

                        copy(
                            &format!("data/{}/2_OPTIMIZATION.xyz", vacuum_censo_path),
                            &format!("data/{}/vacuum_censo.xyz", run.local_path),
                        )?;

                        run_program(vec![
                            "python",
                            "trim_xyz.py",
                            &format!("data/{}/vacuum_censo.xyz", run.local_path),
                        ])?;

                        run_program(vec![
                            "python",
                            "orca.py",
                            &format!("{}", run.local_path),
                            &format!("{:?}", run.remote_host),
                            match &run.run_type {
                                RunType::ORCA => "M062X",
                                RunType::ORCAr2SCAN3c => "r2SCAN-3c",
                                run_type => todo!("{:?}", run_type)
                            },
                        ])?;
                    }
                    _ => todo!("{:?}", run.run_type),
                }

                // copy to server
                run_program(vec![
                    "rsync",
                    "-rv",
                    &format!("data/{}/", run.local_path),
                    &format!("{}:{}", run.remote_host.get_data_host(), run.remote_path),
                ])?;

                // start remote job
                submit_job(&run)?;

                println!(
                    "{:?}",
                    update_run_status(run.local_path, StatusType::Running, &connection)
                );

                match run.run_type.get_resource_type() {
                    RunResourceType::Cpu => match run.remote_host {
                        RemoteHostType::localhost => {}
                        RemoteHostType::katana => katana_cpu_queue_length += 1,
                        RemoteHostType::katana2 => katana2_cpu_queue_length += 1,
                        RemoteHostType::gadi => gadi_queue_length += 1,
                        RemoteHostType::setonix => setonix_queue_length += 1,
                    },
                    RunResourceType::Gpu => match run.remote_host {
                        RemoteHostType::localhost => {}
                        RemoteHostType::katana => katana_gpu_queue_length += 1,
                        RemoteHostType::katana2 => katana2_gpu_queue_length += 1,
                        RemoteHostType::gadi => todo!("gadi using gpu!"),
                        RemoteHostType::setonix => todo!("setonix using gpu!"),
                    },
                }
            }
            StatusType::Running => {
                if !jobs.iter().any(|name| name == &run.local_path) {
                    receive_files(run, &connection)?;
                }
            }
            StatusType::Received => {}
            StatusType::Finished => {}
            StatusType::Failed => {}
        }
    }

    println!("Generating Jobs");


    if planned_cpu < 5 {
        for _ in 1..10 {
            // ORCA
            let mut statement = connection.prepare(
                "\
                    SELECT * FROM molecules \
                    WHERE compound_id NOT IN (SELECT compound_id FROM runs WHERE run_type == 'ORCA') \
                    AND compound_id IN (SELECT compound_id FROM runs WHERE run_type == 'CENSO' AND status == 'Received') \
                    AND compound_id IN (SELECT compound_id FROM runs WHERE run_type == 'VacuumCENSO' AND status == 'Received') \
                    AND compound_id IN (SELECT compound_id FROM runs WHERE run_type == 'FrozenBarCENSO3' AND status == 'Received') \
                ",
            )?;

            match serde_rusqlite::from_rows::<Molecule>(statement.query([])?)
                .next()
                .ok_or(())
            {
                Ok(molecule) => {
                    let query = format!(
                        "INSERT INTO runs (compound_id, run_type, status, remote_host, remote_path) VALUES ('{}', '{:?}', '{:?}', '{:?}', '{}')",
                        molecule?.compound_id,
                        RunType::ORCA,
                        StatusType::Planned,
                        RemoteHostType::localhost,
                        "/dev/null/"
                    );
                    println!("{}", query);
                    connection.execute(&query, [])?;
                }
                Err(_) => {}
            }
        }
        for _ in 1..10 {
            // ORCAr2SCAN3c
            let mut statement = connection.prepare(
                "\
                    SELECT * FROM molecules \
                    WHERE compound_id NOT IN (SELECT compound_id FROM runs WHERE run_type == 'ORCAr2SCAN3c') \
                    AND compound_id IN (SELECT compound_id FROM runs WHERE run_type == 'CENSO' AND status == 'Received') \
                    AND compound_id IN (SELECT compound_id FROM runs WHERE run_type == 'VacuumCENSO' AND status == 'Received') \
                ",
            )?;

            match serde_rusqlite::from_rows::<Molecule>(statement.query([])?)
            .next()
            .ok_or(())
            {
                Ok(molecule) => {
                    let query = format!(
                        "INSERT INTO runs (compound_id, run_type, status, remote_host, remote_path) VALUES ('{}', '{:?}', '{:?}', '{:?}', '{}')",
                        molecule?.compound_id,
                        RunType::ORCAr2SCAN3c,
                        StatusType::Planned,
                        RemoteHostType::localhost,
                        "/dev/null/"
                    );
                    println!("{}", query);
                    connection.execute(&query, [])?;
                }
                Err(_) => {}
            }
        }
        /*{
            // CREST
            let mut statement = connection.prepare(
                "\
                    SELECT * FROM molecules \
                    WHERE compound_id NOT IN (SELECT compound_id FROM runs WHERE run_type == 'CREST') \
                    ORDER BY rotatable_bonds DESC, num_atoms DESC LIMIT 1\
                ",
            )?;

            match serde_rusqlite::from_rows::<Molecule>(statement.query([])?)
                .next()
                .ok_or(())
            {
                Ok(molecule) => {
                    let query = format!(
                        "INSERT INTO runs (compound_id, run_type, status, remote_host, remote_path) VALUES ('{}', '{:?}', '{:?}', '{:?}', '{}')",
                        molecule?.compound_id,
                        RunType::CREST,
                        StatusType::Planned,
                        RemoteHostType::localhost,
                        "/dev/null/"
                    );
                    println!("{}", query);
                    connection.execute(&query, [])?;
                }
                Err(_) => {}
            }
        }*/

        /*{
            let mut statement = connection.prepare(
                "\
                    SELECT * FROM molecules \
                    WHERE compound_id NOT IN (SELECT compound_id FROM runs WHERE run_type == 'VacuumCENSO') \
                    AND compound_id IN (SELECT compound_id FROM runs WHERE run_type == 'VacuumCREST' AND status == 'Received') \
                    ORDER BY rotatable_bonds ASC LIMIT 1\
                ",
            )?;

            match serde_rusqlite::from_rows::<Molecule>(statement.query([])?)
                .next()
                .ok_or(())
            {
                Ok(molecule) => {
                    let query = format!(
                        "INSERT INTO runs (compound_id, run_type, status, remote_host, remote_path) VALUES ('{}', '{:?}', '{:?}', '{:?}', '{}')",
                        molecule?.compound_id,
                        RunType::VacuumCENSO,
                        StatusType::Planned,
                        RemoteHostType::localhost,
                        "/dev/null/"
                    );
                    println!("{}", query);
                    connection.execute(&query, [])?;
                }
                Err(_) => {}
            }
        }*/
        {
            let mut statement = connection.prepare(
                "\
                    SELECT * FROM molecules \
                    WHERE compound_id NOT IN (SELECT compound_id FROM runs WHERE run_type == 'FrozenForwardCENSO3') \
                    AND compound_id IN (SELECT compound_id FROM runs WHERE run_type == 'FrozenMinEquilCENSO3' AND status == 'Received') \
                    ORDER BY rotatable_bonds DESC LIMIT 1\
                ",
            )?;

            match serde_rusqlite::from_rows::<Molecule>(statement.query([])?)
                .next()
                .ok_or(())
            {
                Ok(molecule) => {
                    let query = format!(
                        "INSERT INTO runs (compound_id, run_type, status, remote_host, remote_path) VALUES ('{}', '{:?}', '{:?}', '{:?}', '{}')",
                        molecule?.compound_id,
                        RunType::FrozenForwardCENSO3,
                        StatusType::Planned,
                        RemoteHostType::localhost,
                        "/dev/null/"
                    );
                    println!("{}", query);
                    connection.execute(&query, [])?;
                }
                Err(_) => {}
            }
        }
        for _ in 0..2 {
            let mut statement = connection.prepare(
                "\
                    SELECT * FROM molecules \
                    WHERE compound_id NOT IN (SELECT compound_id FROM runs WHERE run_type == 'FrozenReversedCENSO3') \
                    AND compound_id IN (SELECT compound_id FROM runs WHERE run_type == 'FrozenForwardCENSO3') \
                    AND compound_id IN (SELECT compound_id FROM runs WHERE run_type == 'FrozenMinEquilCENSO3' AND status == 'Received') \
                    ORDER BY rotatable_bonds DESC LIMIT 1\
                ",
            )?;

            match serde_rusqlite::from_rows::<Molecule>(statement.query([])?)
                .next()
                .ok_or(())
            {
                Ok(molecule) => {
                    let query = format!(
                        "INSERT INTO runs (compound_id, run_type, status, remote_host, remote_path) VALUES ('{}', '{:?}', '{:?}', '{:?}', '{}')",
                        molecule?.compound_id,
                        RunType::FrozenReversedCENSO3,
                        StatusType::Planned,
                        RemoteHostType::localhost,
                        "/dev/null/"
                    );
                    println!("{}", query);
                    connection.execute(&query, [])?;
                }
                Err(_) => {}
            }
        }
    }
    for _ in 0..2 {
        // VacuumCREST
        let mut statement = connection.prepare(
            "\
                SELECT * FROM molecules \
                WHERE compound_id NOT IN (SELECT compound_id FROM runs WHERE run_type == 'VacuumCREST') \
                ORDER BY rotatable_bonds ASC LIMIT 1\
            ",
        )?;

        match serde_rusqlite::from_rows::<Molecule>(statement.query([])?)
            .next()
            .ok_or(())
        {
            Ok(molecule) => {
                let query = format!(
                    "INSERT INTO runs (compound_id, run_type, status, remote_host, remote_path) VALUES ('{}', '{:?}', '{:?}', '{:?}', '{}')",
                    molecule?.compound_id,
                    RunType::VacuumCREST,
                    StatusType::Planned,
                    RemoteHostType::localhost,
                    "/dev/null/"
                );
                println!("{}", query);
                connection.execute(&query, [])?;
            }
            Err(_) => {}
        }
    }
    if planned_gpu >= 5 {
        return Ok(());
    }

    for _ in 0..2 {
        let mut statement = connection.prepare("\
        SELECT * FROM molecules \
        WHERE compound_id NOT IN (SELECT compound_id FROM runs WHERE run_type == 'RelaxedReversedGAFF') \
        AND compound_id IN (SELECT compound_id FROM runs WHERE run_type == 'RelaxedForwardGAFF') \
        AND compound_id IN (SELECT compound_id FROM runs WHERE run_type == 'RelaxedMinEquilGAFF' AND status == 'Received') \
        ORDER BY rotatable_bonds ASC, num_atoms ASC LIMIT 1\
    ")?;

        match serde_rusqlite::from_rows::<Molecule>(statement.query([])?)
            .next()
            .ok_or(())
        {
            Ok(molecule) => {
                let query = format!(
                    "INSERT INTO runs (compound_id, run_type, status, remote_host, remote_path) VALUES ('{}', '{:?}', '{:?}', '{:?}', '{}')",
                    molecule?.compound_id,
                    RunType::RelaxedReversedGAFF,
                    StatusType::Planned,
                    RemoteHostType::localhost,
                    "/dev/null/"
                );
                println!("{}", query);
                connection.execute(&query, [])?;
            }
            Err(_) => {}
        }
    }

    {
        let mut statement = connection.prepare("\
            SELECT * FROM molecules \
            WHERE compound_id NOT IN (SELECT compound_id FROM runs WHERE run_type == 'RelaxedForwardGAFF') \
            AND compound_id IN (SELECT compound_id FROM runs WHERE run_type == 'RelaxedMinEquilGAFF' AND status == 'Received') \
            ORDER BY rotatable_bonds ASC, num_atoms ASC LIMIT 5\
        ")?;
        match serde_rusqlite::from_rows::<Molecule>(statement.query([])?)
            .next()
            .ok_or(())
        {
            Ok(molecule) => {
                let query = format!(
                    "INSERT INTO runs (compound_id, run_type, status, remote_host, remote_path) VALUES ('{}', '{:?}', '{:?}', '{:?}', '{}')",
                    molecule?.compound_id,
                    RunType::RelaxedForwardGAFF,
                    StatusType::Planned,
                    RemoteHostType::localhost,
                    "/dev/null/"
                );
                println!("{}", query);
                connection.execute(&query, [])?;
            }
            Err(_) => {}
        }
    }

    Ok(())
}
