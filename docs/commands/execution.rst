Execution & Monitoring
======================

Commands for running workflows and inspecting their status.

* ``submit --runner RUNNER`` – Submit the current task for execution
* ``status [--wait]`` – Inspect status, optionally polling to a terminal state
* ``cancel`` – Cancel running impressions for the current task or directory
* ``log INDEX`` – Read a user-command log; ``--follow`` polls for new content
* ``engine-logs`` – Inspect workflow-engine logs
* ``collect`` – Copy selected results into Yuki storage
* ``collect-outputs`` / ``collect-logs`` – Collect only outputs or logs
* ``check-results RUNNER`` – Mount cached results for inspection on an SSH runner
* ``display FILE`` – Open a result file in the default browser
* ``export [GLOB]`` – Export matching results to the project's export directory
