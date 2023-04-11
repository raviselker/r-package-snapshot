
# r-package-snapshot

this relies on 4 secrets:

 - `SSH_CONFIG`
 - `KNOWN_HOSTS`
 - `SSH_PRIVATE_KEY`
 - `REPO_DIR`

### SSH_CONFIG

the content of this secret is placed at `~/.ssh/config` (the standard ssh config location) and is of the form:

```
Host repo
    HostName jamovi.org
    User <username goes here>
```

### KNOWN_HOSTS

the content of this secret is placed at `~/.ssh/known_hosts` (the standard known_hosts location).

you should populate it with the output from the `ssh-keyscan jamovi.org` command.

### SSH_PRIVATE_KEY

the private key to ssh into the server with. the content of this secret will be written to `~/.ssh/id_rsa` (again, this is standard ssh stuff).

### REPO_DIR

this should contain the directory where the repo should be uploaded to. i.e. `~/repo.jamovi.org`


