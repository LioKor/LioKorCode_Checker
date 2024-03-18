import subprocess


def checker(fix: bool) -> None:
    folders_to_check = ("src", "tests", "scripts")

    format_args = () if fix else ("--check",)
    lint_args = ("--fix",) if fix else ()

    checks = {
        "POETRY_GENERAL": ("poetry", "check"),
        "POETRY_LOCK": ("poetry", "check", "--lock"),
        "FORMAT": ("ruff", "format", *folders_to_check, *format_args),
        "LINT": ("ruff", "check", *folders_to_check, *lint_args),
        "TYPING": ("pyright", *folders_to_check),
        "TESTS": ("python", "-m", "unittest"),
    }

    print(f"🐺🐺🐺 Checking folders {folders_to_check} and running tests using wolf's power (🐺)")
    print(f"Autofix is {'✅  ENABLED' if fix else '❗  DISABLED'}")
    for check_name, check_command in checks.items():
        print(f"⌛ Checking {check_name}...")
        try:
            stdout = subprocess.check_output(check_command)
            output = stdout.decode().split("\n")
            if len(output) > 10:
                output = [output[-2]]
            for line in output:
                if line:
                    print(f"   * {line}")
        except subprocess.CalledProcessError as err:
            print("❗❗❗ CHECK FAILED ❗❗❗ ")
            print(err.stdout.decode())
            exit(1)
    print("✅ ✅ ✅  ALL CHECKS HAVE PASSED ✅ ✅ ✅ ")
    if fix:
        print("⚠️ Don't forget to commit changed files after autofix if there are any.")


def check_no_fix() -> None:
    checker(fix=False)


def check_and_fix() -> None:
    checker(fix=True)
