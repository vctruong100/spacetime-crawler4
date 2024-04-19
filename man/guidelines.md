## Guidelines
You should follow these guidelines as you work on the repo.

### Commit Messages
Commit messages should be scoped by feature. For example: if you are working on `utils/panic.c`, format your 
message like this: `utils/panic: [message]`. Messages should be imperative. Good messages include: `Fix typo` or 
`Add tests`. Bad messages include: `Adds this` or `Removed this`.

Here are a few examples:
- `readme: Fix typo`
- `scraper: Remove debug messages to reduce unwanted output`
- `clib/man: Add translations for de_DE`

### Branching
Please do not work on the `master` branch! Work on features by switching to another branch. The branch should be 
named appropriately based on the feature you are working on. Remember to sync your repo before you create/switch 
branches.

To sync your repo:
```bash
$ git fetch origin
$ git merge origin/master

# alternatively:
$ git pull origin master
```

To create and switch to a branch:
```bash
$ git checkout -b my-branch
```

To switch to a branch:
```bash
$ git checkout my-branch
```

To bring in changes from `master` branch to your local branch:
```bash
$ git checkout my-branch
$ git rebase master
```

When you are done implementing a feature, merge with the `master` branch and update the repo:
```bash
$ git checkout master
$ git pull origin master    # sync master branch
$ git merge my-branch       # branch to merge
$ git branch -d my-branch   # delete branch
$ git push origin           # update remote repo
```

If your changes in `master` branch are synced to your local branch, and you want 
to merge local branch while making the merge explicit (shows up in commit tree) 
(e.g. you want to merge a LARGE feature), add the `--no-ff` flag when merging:
```bash
$ git merge --no-ff my-branch
```
