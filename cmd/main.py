import argparse
import subprocess
import sys

import app
from .consts import *
from .utils import *

run_maim_file = Path(sys.argv[0])
service_filename = f'{Path(NAME).stem}.service'
timer_filename = f'{Path(NAME).stem}.timer'
config_filename = Path(INSTALL_CONFIG_PATH).joinpath(CONFIG_FILENAME)
bin_filename = Path(INSTALL_BIN_PATH).joinpath(Path(NAME).name)
venv_dir = run_maim_file.parent.joinpath(VENV_DIR_NAME)
venv_python = venv_dir.joinpath(BIN_NAME).joinpath(PYTHON_NAME)


def check_root():
    if not is_root():
        print('需要以 root 权限运行!')
        exit(os.EX_NOPERM)


def gen_config(filename: str | Path):
    write_file(filename, EXAMPLE_CONFIG_FILE)


def gen_config_interactive(filename: str | Path):
    print('选择 let\'s encrypt API')
    opt = [f'{PRODUCTION_URL} (生产环境)',
           f'{STAGING_URL} (测试环境)']
    env = input_select('12', opt)
    if env == '1':
        directory = PRODUCTION_URL
    else:
        directory = STAGING_URL

    access_key_id = input_string('阿里云 Access key ID')
    access_key_secret = input_string('阿里云 Access key secret')
    email = input_string('邮箱')

    domains = list[str]()
    domains.append(input_string('域名'))
    while input_yes_no('是否继续添加域名？'):
        domains.append(input_string('域名'))

    write_str = VAR_APP_CONFIG.format(
        directory=directory,
        access_key_id=access_key_id,
        access_key_secret=access_key_secret,
        email=email
    )

    for d in domains:
        write_str += VAR_DOMAIN_CONFIG.format(domain=d)

    write_file(filename, write_str)


def gen_service(config_path: str, save_dir: str = '.'):
    filename = Path(save_dir).joinpath(service_filename)
    data = EXAMPLE_SERVICE_FILE.format(wd=f'{run_maim_file.parent}',
                                       exec=f'{run_maim_file.absolute()} -c {Path(config_path).absolute()}')
    write_file(filename, data, re_name=False)


def gen_timer(save_dir: str = '.'):
    filename = Path(save_dir).joinpath(timer_filename)
    write_file(filename, EXAMPLE_TIMER_FILE, re_name=False)


def gen_systemd(config_path: str, is_install: bool = False, user: bool = False):
    if is_install:
        if user:
            gen_service(config_path, SYSTEMD_DIR_USER)
            gen_timer(SYSTEMD_DIR_USER)
        else:
            check_root()
            gen_service(config_path, SYSTEMD_DIR)
            gen_timer(SYSTEMD_DIR)
    else:
        gen_service(config_path)
        gen_timer()


def install(interactive=False):
    check_root()

    copy(run_maim_file.parent, INSTALL_DEP_PATH)
    link_file = Path(INSTALL_DEP_PATH).joinpath(run_maim_file.name)
    link(link_file, bin_filename)
    print(f'chmod 755 {run_maim_file}')
    link_file.chmod(755)

    install_venv(Path(INSTALL_DEP_PATH))

    if interactive:
        gen_config_interactive(config_filename)
    else:
        gen_config(config_filename)
    gen_systemd(str(config_filename), True)

    Systemctl.reload()
    Systemctl.enable(timer_filename)
    Systemctl.start(service_filename)
    Systemctl.start(timer_filename)


def uninstall():
    check_root()

    Systemctl.disable(timer_filename)
    Systemctl.stop(timer_filename)
    Systemctl.stop(service_filename)
    remove_files = [
        Path(SYSTEMD_DIR).joinpath(timer_filename),
        Path(SYSTEMD_DIR).joinpath(service_filename),
        bin_filename,
        config_filename,
        Path(INSTALL_DEP_PATH)
    ]

    for file in remove_files:
        remove(file)

    Systemctl.reload()


def install_venv(install_dir: Path = run_maim_file.parent):
    if venv_dir.exists():
        remove(venv_dir)

    cmd(f'{sys.executable} -m venv {install_dir.joinpath(VENV_DIR_NAME)}')
    cmd(f'{install_dir.joinpath(VENV_DIR_NAME).joinpath(BIN_NAME).joinpath(PIP_NAME)}'
        f' install -r {install_dir.joinpath(REQUIREMENTS_NAME)}')


def run():
    if venv_python.absolute() != Path(sys.executable):
        if not venv_dir.exists():
            install_venv()
        ret = subprocess.run([str(venv_python.absolute())] + sys.argv)
        exit(ret.returncode)
    app.main()


def main():
    parser = argparse.ArgumentParser(
        prog=f'python {run_maim_file.name}',
        description='自动申请 SSL 证书和续签，使用阿里云 DNS 验证。')

    sel = ['gen-systemd', 'gen-systemd-i', 'gen-systemd-i-u', 'gen-config', 'gen-config-i', 'install', 'install-i',
           'uninstall']
    parser.add_argument('option', nargs='?', choices=sel)
    parser.add_argument('-c', dest='config', default=f'./{CONFIG_FILENAME}')
    args = parser.parse_args()

    match args.option:
        case None:
            run()
        case 'gen-config':
            gen_config(args.config)
        case 'gen-config-i':
            gen_config_interactive(args.config)
        case 'gen-systemd':
            gen_systemd(args.config)
        case 'gen-systemd-i':
            gen_systemd(args.config, is_install=True)
        case 'gen-systemd-i-u':
            gen_systemd(args.config, is_install=True, user=True)
        case 'install':
            install()
        case 'install-i':
            install(interactive=True)
        case 'uninstall':
            uninstall()
