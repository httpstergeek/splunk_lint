Splunk_lint
====================

This is a basic Splunk linter which is intended to be ran with a Jenkins and git
hook.  The Jenkins would push the repo to a stand along splunk Server and run
the Splunk startup process.  If any config is invalid or causes a failure to
start build will fail.  After verification app is removed.

**NOTE: Replace All Attributes with values for your ENV**

## Requirements
  * python 2.7.x
  * Jenkins
  * Git hook


### Platforms

This cookbook was tested on RHEL6 servers and Mac 10.9.x
