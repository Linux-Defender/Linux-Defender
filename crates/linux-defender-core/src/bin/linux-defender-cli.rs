fn main() {
    let args = std::env::args().skip(1).collect::<Vec<_>>();
    std::process::exit(linux_defender_core::cli::run(&args));
}
