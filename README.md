# Backup Github Repositories to Synology NAS

This repository contains a script which backs up all repositories of a Github user or organization and instructions on how to set up a task on a Synology NAS to automatically backup all repositories.

## Features

- ✅ No external dependencies, except for Python 3 and `git`.
- ✅ Semi-smart backup: Only mirrors repositories which have changed since the last backup to save time and space.
- ✅ Backup all repositories of a user or organization.
- ✅ Keep all past backups (so force pushing to a repository does not destroy the backup).

## Generating a Github Token

You need a Github token to access private repositories. You can generate new fine-grained tokens in the [developer settings](https://github.com/settings/tokens?type=beta) of your Github account.

Select the token owner (your account or an organization), give the token a name and select "All repositories" if you want to backup all private repositories.

You need to set the following permissions:

- Repository permissions > Contents: Read
- Repository permissions > Metadata: Read

After selecting the permissions, click on "Generate token" and copy the token. You can't see the token again, so make sure to save it in a safe place.

## Usage on any machine

Backup script is self-contained and can be run on any machine with Python 3 and `git` installed. You don't even need to clone this repository, just download the `backup.py` file and run it.

```bash
# Backup all repositories of a user
python3 backup.py --user <username> --token <github_token> --path <backup_dir>
# Backup all repositories of an organization
python3 backup.py --organization <organization> --token <github_token> --path <backup_dir>
```

If you want to backup only public repositories, you can omit the `--token` argument.

## Configuration on Synology NAS

We will create a new task in the Task Scheduler of the Synology DSM to automatically backup all repositories of a Github user or organization every day, week, or month.

0. Make sure you have `python3` and `git` installed on your Synology NAS. You can install Python 3 from the Package Center. The easiest way to install `git` is to use the [SynoCommunity](https://synocommunity.com/) package source. Another option is to install Git Server from the Package Center, but it is a bit overkill for just using the `git` command.
1. Create new folder for the backups in the File Station. For example, create a new folder called `github-backups` in the `home` directory (you might want to create a separate user for the backups).
2. Copy the `backup.py` script to the new folder (putting this `README.md` file there is also a good idea).
3. Open the Task Scheduler in the Control Panel.

> [!NOTE]
> In Task Scheduler settings, you can set the output folder for the script to simplify the debugging.

4. Select "Scheduled task" > "User-defined script".
5. Name the task, for example "Github Backup" (maybe add the user or organization name in case of backing up multiple users).
6. In "Schedule" tab, set the schedule to your liking (e.g. once per day at 3:00 AM).
7. In "Task Settings" tab, set notification settings so you will be notified if the backup fails:
   - Check "Send run details by email" and enter your email address.
   - Check "Send run details only when the script terminates abnormally" to only receive emails when the backup fails.
   - Note that you need to set up email notifications in the Control Panel > Notification > Email first.
8. Now, we can finally add the script to the task. Under "Run command" enter the command below:

   ```bash
   python3 /volume1/homes/<synology-user-name>/github-backups/backup.py --user <username> --token <github_token> --path /volume1/homes/<synology-user-name>/github-backups
   ```

   - Do not forget to change the path to the `backup.py` script and the backup directory.
   - Replace `<username>` with the Github username or specify the organization with `--organization <organization>`.
   - Replace `<github_token>` with the Github token.

9. Click "OK" to save the task. You can run the task manually to test if everything works as expected.
