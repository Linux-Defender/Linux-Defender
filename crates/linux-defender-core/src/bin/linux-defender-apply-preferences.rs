fn main() {
    let args: Vec<String> = match std::env::args_os()
        .skip(1)
        .map(|arg| arg.into_string())
        .collect::<Result<Vec<_>, _>>()
    {
        Ok(args) => args,
        Err(_) => {
            eprintln!("error: privileged helper arguments must be valid UTF-8");
            std::process::exit(2);
        }
    };
    std::process::exit(linux_defender_core::privileged::run_helper(&args));
}
