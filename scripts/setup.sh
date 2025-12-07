celebi-navigate() {
workdir="$(python - <<'EOF'
from Chern.interface.ChernManager import ChernProjectManager
manager = ChernProjectManager().get_manager()
project_name=manager.get_current_project()
print(manager.get_project_path(project_name))
EOF
)"
cd $workdir
}

celebi-ls() {
python - <<'EOF'
from Chern.interface.shell import ls
print(ls("").colored())
EOF
}

celebi-status() {
python - <<'EOF'
from Chern.interface.shell import status
print(status().colored())
EOF
}

celebi-cd() {
python - "$1" <<'EOF'
from Chern.interface.shell import cd
import sys
cd(sys.argv[1])
EOF
}

celebi-cdproject() {
python - "$1" <<'EOF'
from Chern.interface.shell import shell_cd_project
import sys
shell_cd_project(sys.argv[1])
EOF
}

celebi-mv() {
python - "$1" "$2" <<'EOF'
from Chern.interface.shell import mv
import sys
mv(sys.argv[1], sys.argv[2])
EOF
}

celebi-cp() {
python - "$1" "$2" <<'EOF'
from Chern.interface.shell import cp
import sys
cp(sys.argv[1], sys.argv[2])
EOF
}

celebi-rm() {
python - "$1" <<'EOF'
from Chern.interface.shell import rm
import sys
rm(sys.argv[1])
EOF
}

celebi-short-ls() {
python - <<'EOF'
from Chern.interface.shell import short_ls
short_ls("")
EOF
}

celebi-jobs() {
python - <<'EOF'
from Chern.interface.shell import jobs
jobs("")
EOF
}

celebi-mkalgorithm() {
python - "$1" <<'EOF'
from Chern.interface.shell import mkalgorithm
import sys
mkalgorithm(sys.argv[1])
EOF
}

celebi-mktask() {
python - "$1" <<'EOF'
from Chern.interface.shell import mktask
import sys
mktask(sys.argv[1])
EOF
}

celebi-mkdata() {
python - "$1" <<'EOF'
from Chern.interface.shell import mkdata
import sys
mkdata(sys.argv[1])
EOF
}

celebi-mkdir() {
python - "$1" <<'EOF'
from Chern.interface.shell import mkdir
import sys
mkdir(sys.argv[1])
EOF
}

celebi-rmfile() {
python - "$1" <<'EOF'
from Chern.interface.shell import rm_file
import sys
rm_file(sys.argv[1])
EOF
}

celebi-mvfile() {
python - "$1" "$2" <<'EOF'
from Chern.interface.shell import mv_file
import sys
mv_file(sys.argv[1], sys.argv[2])
EOF
}

celebi-import() {
python - "$1" <<'EOF'
from Chern.interface.shell import import_file
import sys
import_file(sys.argv[1])
EOF
}

celebi-add-input() {
python - "$1" "$2" <<'EOF'
from Chern.interface.shell import add_input
import sys
add_input(sys.argv[1], sys.argv[2])
EOF
}

celebi-remove-input() {
python - "$1" <<'EOF'
from Chern.interface.shell import remove_input
import sys
remove_input(sys.argv[1])
EOF
}

celebi-add-algorithm() {
python - "$1" <<'EOF'
from Chern.interface.shell import add_algorithm
import sys
add_algorithm(sys.argv[1])
EOF
}

celebi-add-parameter() {
python - "$1" "$2" <<'EOF'
from Chern.interface.shell import add_parameter
import sys
add_parameter(sys.argv[1], sys.argv[2])
EOF
}

celebi-rm-parameter() {
python - "$1" <<'EOF'
from Chern.interface.shell import rm_parameter
import sys
rm_parameter(sys.argv[1])
EOF
}

celebi-add-parameter-subtask() {
python - "$1" "$2" "$3" <<'EOF'
from Chern.interface.shell import add_parameter_subtask
import sys
add_parameter_subtask(sys.argv[1], sys.argv[2], sys.argv[3])
EOF
}

celebi-set-env() {
python - "$1" <<'EOF'
from Chern.interface.shell import set_environment
import sys
set_environment(sys.argv[1])
EOF
}

celebi-set-mem() {
python - "$1" <<'EOF'
from Chern.interface.shell import set_memory_limit
import sys
set_memory_limit(sys.argv[1])
EOF
}

celebi-hosts() {
python - <<'EOF'
from Chern.interface.shell import hosts
hosts()
EOF
}

celebi-add-host() {
python - "$1" "$2" <<'EOF'
from Chern.interface.shell import add_host
import sys
add_host(sys.argv[1], sys.argv[2])
EOF
}

celebi-runners() {
python - <<'EOF'
from Chern.interface.shell import runners
runners()
EOF
}

celebi-register-runner() {
python - "$1" "$2" "$3" <<'EOF'
from Chern.interface.shell import register_runner
import sys
register_runner(sys.argv[1], sys.argv[2], sys.argv[3])
EOF
}

celebi-remove-runner() {
python - "$1" <<'EOF'
from Chern.interface.shell import remove_runner
import sys
remove_runner(sys.argv[1])
EOF
}

celebi-send() {
python - "$1" <<'EOF'
from Chern.interface.shell import send
import sys
send(sys.argv[1])
EOF
}

celebi-submit() {
python - "$1" <<'EOF'
from Chern.interface.shell import submit
import sys
runner = sys.argv[1] if len(sys.argv) > 1 else "local"
submit(runner)
EOF
}

celebi-view() {
python - "$1" <<'EOF'
from Chern.interface.shell import view
import sys
browser = sys.argv[1] if len(sys.argv) > 1 else "open"
view(browser)
EOF
}

celebi-edit() {
python - "$1" <<'EOF'
from Chern.interface.shell import edit_script
import sys
edit_script(sys.argv[1])
EOF
}

celebi-config() {
python - <<'EOF'
from Chern.interface.shell import config
config()
EOF
}

celebi-danger() {
python - "$1" <<'EOF'
from Chern.interface.shell import danger_call
import sys
danger_call(sys.argv[1])
EOF
}

celebi-trace() {
python - "$1" <<'EOF'
from Chern.interface.shell import trace
import sys
trace(sys.argv[1])
EOF
}

celebi-history() {
python - <<'EOF'
from Chern.interface.shell import history
print(history().colored())
EOF
}

celebi-changes() {
python - <<'EOF'
from Chern.interface.shell import changes
print(changes().colored())
EOF
}


celebi-preshell() {
python - <<'EOF'
from Chern.interface.shell import workaround_preshell
print(workaround_preshell())
EOF
}

celebi-postshell() {
python - <<'EOF'
from Chern.interface.shell import workaround_postshell
workaround_postshell()
EOF
}

sys-cp() {
cp "$@"
}
alias cp='celebi-cp'
sys-mv() {
mv "$@"
}
alias mv='celebi-mv'
sys-mkdir() {
mkdir "$@"
}
alias mkdir='celebi-mkdir'

alias status='celebi-status'
alias navigate='celebi-navigate'
alias history='celebi-history'
alias changes='celebi-changes'
alias jobs='celebi-jobs'
alias cdproject='celebi-cdproject'
alias mkalgorithm='celebi-mkalgorithm'
alias mktask='celebi-mktask'
alias mkdata='celebi-mkdata'
alias rm='celebi-rm'
alias rmfile='celebi-rmfile'
alias mvfile='celebi-mvfile'
alias import='celebi-import'
alias add-input='celebi-add-input'
alias remove-input='celebi-remove-input'
alias add-algorithm='celebi-add-algorithm'
alias add-parameter='celebi-add-parameter'
alias rm-parameter='celebi-rm-parameter'
alias add-parameter-subtask='celebi-add-parameter-subtask'
alias set-env='celebi-set-env'
alias set-mem='celebi-set-mem'
alias hosts='celebi-hosts'
