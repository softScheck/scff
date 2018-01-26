# softScheck Cloud Fuzzing Framework

The softScheck Cloud Fuzzing Framework (sCFF) is a set of tools, aiming to make
Cloud fuzzing easy. It aims to become a framework where fuzzers and other cloud
services can easily be added. At the moment it is still a rather hard coded
tool set to save a lot of time when fuzzing in the Amazon cloud. It helps and
guides the user through the deployment, fuzzing itself, as well as the post fuzzing phase, in which findings must be examined.

![scff-ctrl](https://www.softscheck.com/assets/img/blog/scff-ctrl.png)

This readme just covers the basics. There is also a [Tutorial](https://www.softscheck.com/en/identifying-security-vulnerabilities-with-cloud-fuzzing) showing how to identify real life vulnerabilities with sCFF and an 
[paper](https://www.softscheck.com/papers/Pohl_Kirsch_scff_paper_170405.pdf) which covers technical details.

## Quickstart

This chapter covers the installation, AWS setup, first run and scff-demo to demonstrate the basic workflow.

### Installation

Get sCFF from the GitHub repository:
```bash
git clone https://github.com/softscheck/scff.git
cd scff
```

If you have a Debian-based distribution, you can generate a Debian package (`./mkdeb.sh`) and install it aferwards. Some distributions won't have the python3-boto3 package, though, resulting in a failure. In this case, you have to use the method below.

```bash
pip3 install .
# OR
easy_install3 . 
```
Otherwise install python3-boto3 and run `python3 ./setup.py install`.
In case installation will fail with a permission denied error, install as root.

### AWS account creation and configuration

Because the only Cloud provider currently supported by sCFF is Amazon, an AWS account is required. You can create one at <https://aws.amazon.com>
Once, finished you need to export your key_id and the corresponding aws_secrect_key aswell. It is recommended not to export the root keys and instead to create and export an IAM with the minimal set of required permissions (scff requires the EC2 policies).

Add the keys to the file .aws/credentials like that
```ini
[default]
aws_access_key_id = Access key id
aws_secret_access_key = Secret access key
```

Also, add your amazon region to .aws/config. If you don't know your region, open
the amazon management console and look at the URL ;)
Example contents of .aws/config:
```ini
[default]
region = eu-central-1
output = text
``` 

You should now be able to connect to AWS with sCFF. To check if everything is
working without doing anything type: `scff-ctrl`

While we are now able to manage EC2 instance from within our tool, we are still
not able to connect to an EC2 instance. Todo you have to create an SSH key pair first.
Save the key pair as ~/.scff/aws-key-pair.pem.

Next, create a Security Group with the name *SSH*. Allow TCP traffic from port 22.
Allow internal traffic and if you wish to see what your distributed fuzzers are doing allow traffic to your IP on TCP port 8000.

### Get used to the workflow

Run `scff-demo` to get to know the typical sCFF workflow.


## Fuzzing

Create a new directory and put the program you want to fuzz and a template file, for which the program does not crash, in it.

Then think about how much you are willing to spend and how long you want your machines to run. Execute `scff-costcalc` to get an idea of how much it will cost. Keep in mind that if you are new to the Amazon Cloud you can fuzz for free, if you select the t2.micro instance and keep the runtime below 750 hours.

Now run `scff-mkcfg` and answer the questions to create your project file. The default name of the configuration file is scff.proj. You can review and edit this file with a text editor of your choice. If everything seems fine, start `scff-create-instances`, which will create your instance(s). Wait for them to boot and bootstrap them with `scff-ctrl scff.proj bootstrap`. This will install necessary files on the remote machine and deploy your target. You are now ready to fuzz.

In scff, there are two fuzz modes. Single mode and distributed mode. In single mode, fuzzers on different machines run independently of each other. In distributed mode, they will share their corpus, leading to faster results. Distributed mode is, therefore, the recommended mode. To start distributed mode, run `scff-ctrl scff.proj distributed`.

To check if everything works fine, view the fuzzer status with `scff-ctrl scff.proj status` If the security group permits incoming traffic on port 8000, you can also view the status on your web-browser (SERVER_IP:8000).

Don't forget to stop or terminate the instance, once you are done, otherwise you can end up paying a *lot* very fast.


## Programs

* scff-amisearch: Search AMIs and display basic info
* scff-clean: Removes unused AMIs, snapshots and volumes
* scff-costcalc: Get to know how much *X* machines from type *Y* cost for *Z* hours
* scff-create-instance: Create EC2 instances based on a scff project file
* scff-ctrl: Control EC2 instances as well as the fuzzers
* scff-demo: A wizard like tutorial program
* scff-exploitcheck: Test findings on exploitability
* scff-mkcfg: Create a scff project file
* scff-pocgen: Generate proof of concept scripts
* scff-stats: Display fuzzing statistics

For more information about a single program, view the associated man page.

## FAQ

#### Is it possible to fuzz another program on an existing machine?
Yes, create a new project file, stop the fuzzers and run `scff-ctrl <INSTANCE(s)> clean && scff-ctrl <INSTANCE(s)> bootstrap`.

#### I get errors connecting to the daemon, fuzzers exit immediately, etc.
View log with `scff-ctrl <INSTANCES(s)> log` and try `scff-crtl <INSTANCE(s)> doctor`.

#### I want to use a different fuzzer.
sCFF currently ships with an AFL module only, however you can easily create a new fuzzer module. Simply create a new python script in data/scff/fuzzers. Look at the existing afl and dummy module to get an idea how they should look.

### Do I really have to bootstrap every machine?
No, we recommened to create an scff AMI. To do so, simply create a new instance and run `scff-ctrl <YOU_NEW_INSTANCE> bake-image`. This will create a sCFF ready image you can use next time for your machines. It should be at the bottom of the scff-mkcfg AMI selection. If you create a lot of AMIs, run `scff-clean` from time to time to remove unused images.

#### I don't like the Amazon cloud, what about Google Cloud, Azure, etc?
Currently not supported and it's unlikely that it will be in the next months. Sorry :(

#### I have no bash/zsh completions when installing with pip/easyinstall.
That is normal, pip and easyinstall are not designed to install files in system folders. You can copy the auto complete defintions manually.

```bash
cd data
sudo cp bash-completions/completions/sccf-ctrl /usr/share/bash-completions/completions
sudo cp zsh/vendor-completions/_sccf-ctrl /usr/share/zsh/vendor-completions
```

#### I have found a bug, what should I do?
Create a GitHub issue and/or write a mail to wilfried.kirsch@softscheck.com

