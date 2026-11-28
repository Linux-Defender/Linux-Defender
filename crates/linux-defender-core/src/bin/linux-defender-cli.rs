fn main() {
    // args_os + explicit validation keeps the documented clean exit 2 instead
    // of panicking on a non-Unicode argument (std::env::args() panics).
    let raw = std::env::args_os().skip(1).collect::<Vec<_>>();
    let args = match raw
        .iter()
        .map(|arg| arg.to_str().map(str::to_owned))
        .collect::<Option<Vec<_>>>()
    {
        Some(args) => args,
        None => {
            eprintln!("Linux Defender arguments must be valid Unicode; use the GUI file-selection route for arbitrary filesystem names.");
            std::process::exit(2);
        }
    };
    std::process::exit(linux_defender_core::cli::run(&args));
}
