# Installing virtualenv

First and foremost, we take no credit for the virtualenv project, we're just happy users of it. :)

If you want a quick, let's just install it and move on approach, keep reading! Otherwise head [here](https://www.dabapps.com/blog/introduction-to-pip-and-virtualenv-python/) for a more in-depth approach.

## Install on Ubuntu 14.*
### Prereqs
- Root privileges (able to use sudo)

### Step 1 - Install pip
We need to make sure pip is installed. Run `which pip`. If that commands shows a file path, great! Head to step 2.

Otherwise, install it via `sudo easy_install pip`. Run the `which pip` again to make sure it installed.

### Step 2 - Install virtualenv
Now that we have pip, we'll go get virtualenv. Run `sudo pip install virtualenv`. Just to be safe, we'll verify it installed, `which virtualenv`. If that showed a path, we're good to go! Head back to the README to continue.
