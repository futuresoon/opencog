#! /usr/bin/env python
#
# Libcloud tool to build Rackspace VPS, install Aegir and build makefile-based Drupal projects
# Designed for use as a Jenkins project, works from CLI just fine though
# Dependencies: libcloud, fabric
#
# Written by Miguel Jacq (mig5) of Green Bee Digital and the Aegir project
# http://greenbeedigital.com.au
#

from libcloud.compute.types import Provider
from libcloud.compute.providers import get_driver
from libcloud.compute.ssh import SSHClient, ParamikoSSHClient
import libcloud.security
import os, sys, string, ConfigParser, socket, time, random, traceback
import fabric.api as fabric

libcloud.security.VERIFY_SSL_CERT = True

# Fetch some values from the config file
config = ConfigParser.RawConfigParser()
config.read(os.path.expanduser("~/opencog/opencog_config.ini"))

# Try to abstract the provider here, as we may end up supporting others
# Theoretically since we are using libcloud, it should support any
# provider that supports the deploy_node function (Amazon EC2 doesn't)
provider = config.get('Opencog', 'provider')
provider_driver = config.get(provider, 'driver')

# API credentials
user = config.get(provider, 'user')
key = config.get(provider, 'key')

# Preferred image and size
config_distro = config.get(provider, 'distro')
config_size = config.get(provider, 'size')

# A trusted IP to grant access to in the firewall
#trusted_ip = config.get('Aegir', 'trusted_ip')

hostname = 'opencog-%d' % random.randrange(0, 10001, 2)

# Some basic dependency tests for this job itself
def dependency_check():
        try:   
                import fabric                                   

        except ImportError:
                print "You need Fabric installed (apt-get install fabric)"
                sys.exit(1)

# Helper script to generate a random password
def gen_passwd():
        N=8
        return ''.join(random.choice(string.ascii_letters + string.digits) for x in range(N))

# Install dependencies for Aegir
def fab_install_dependencies(newpass):
	fabric.run("apt-get update", pty=True)
        fabric.run("apt-get -y install bzr", pty=True)
        fabric.run("bzr branch -r40 lp:~opencog-dev/opencog/cogbuntu cogbuntu-11.10", pty=True)
        fabric.run("cd cogbuntu-11.10", pty=True)
        fabric.run("mkdir temp", pty=True)
        fabric.run("./cogbuntu-11.10/install-packages-opencog-dep.sh temp", pty=True)
#        fabric.run("cd cogbuntu-11.10", pty=True)
        fabric.run("apt-get -y install bzr cmake", pty=True)
        fabric.run("apt-get -y install libboost-all-dev libexpat1-dev", pty=True)
        fabric.run("apt-get -y install libboost-date-time-dev libboost-filesystem-dev libboost-regex-dev libboost-program-options-dev libboost-system-dev libboost-signals-dev libboost-thread-dev guile-1.8-dev libxerces-c2-dev libluabind-dev", pty=True)
        fabric.run("cd cogbuntu-11.10 ; bzr branch lp:opencog",pty=True)
        fabric.run("cd cogbuntu-11.10 ; bzr branch opencog ochack", pty=True)
        fabric.run("cd cogbuntu-11.10/ochack ; mkdir bin ; cd bin ; cmake .. ; make", pty=True)
        fabric.run("wget https://launchpad.net/~dhart/+archive/ppa/+files/cxxtest_3.10.1-0ubuntu1~dhart1_all.deb", pty=True)
        fabric.run("dpkg -i cxxtest_3.10.1-0ubuntu1~dhart1_all.deb", pty=True)
        fabric.run("cd cogbuntu-11.10/ochack/bin ; cmake .. ; make ; make test", pty=True)
        fabric.run("aptitude install graphviz doxygen ; cd cogbuntu-11.10/ochack/bin ; cmake .. ; make doxygen ;", pty=True)
        fabric.run("aptitude install guile-1.8-dev ; cd cogbuntu-11.10/ochack/bin ; cmake .. ; make ;", pty=True)
        fabric.run("cp /etc/apt/sources.list /etc/apt/sources.list.backup", pty=True)
        fabric.run("sed -i -e 's/# deb/deb/g\' /etc/apt/sources.list", pty=True)
        fabric.run("aptitude update ; aptitude install libxerces-c2-dev liblua5.1-0-dev libluabind-dev ; cd cogbuntu-11.10/ochack/bin ; cmake .. ; make", pty=True)
        fabric.run("cd cogbuntu-11.10/ochack/bin ; make install ; ldconfig", pty=True)
        fabric.run("sed -i '1 i export PYTHONPATH=/root/cogbuntu-11.10/ochack/bin/opencog/cython:/root/cogbuntu-11.10/ochack/opencog/python:/root/custom/opencog/mindagents' /root/.bashrc", pty=True)
        fabric.run("export PYTHONPATH=/root/cogbuntu-11.10/ochack/bin/opencog/cython:/root/cogbuntu-11.10/ochack/opencog/python:/root/custom/opencog/mindagents", pty=True)
#        fabric.run("", pty=True)


        

# Prepare a basic firewall def fab_prepare_firewall():
        #print "===> Setting a little firewall"
        #fabric.run("iptables -I INPUT -s %s -p tcp --dport 22 -j ACCEPT; iptables -I INPUT -s %s -p tcp --dport 80 -j ACCEPT; iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT; iptables --policy INPUT DROP" % (trusted_ip, trusted_ip), pty=True)


def main():
        # Run some tests
        dependency_check()

	# Set a random password for the MySQL root user.
	newpass = gen_passwd()

        # Make a new connection
        Driver = get_driver( getattr(Provider, provider_driver) )
        conn = Driver(user, key)

        # Get a list of the available images and sizes
        images = conn.list_images()
        sizes = conn.list_sizes()

        # We'll use the distro and size from the config ini
        preferred_image = [image for image in images if config_distro in image.name]
        preferred_size = [size for size in sizes if config_size in size.name]

        # Create and deploy a new server now, and run the deployment steps defined above
        print "Provisioning server and running deployment processes"
        try:
		node = conn.create_node(name=hostname, image=preferred_image[0], size=preferred_size[0])
        except:
		print "Error provisioning new node"
		traceback.print_exc()
                sys.exit(1)


        print "Provisioning complete, you can ssh as root to %s" % node.public_ip[0]
        if node.extra.get('password'):
                print "The root user's password is %s" % node.extra.get('password')
		password = node.extra.get('password')
	

        # VPS aren't immediately available after provisioning sometimes
        # Let's try and loop until the node state is 'Running'.

        var = 1
        while var == 1:
                nodes = conn.list_nodes()
                for node in nodes: 
                        if hostname in node.name:
                                if node.state == 0:
				        # Setting some parameters for fabric
				        domain = socket.getfqdn(node.public_ip[0])
				        fabric.env.host_string = domain
				        fabric.env.user = 'root'
				        fabric.env.password = password

				        try:
				                #fab_prepare_firewall()
				                fab_install_dependencies(newpass)

					        # print "===> Destroying this node"
					        # conn.destroy_node(node)

        	                                var = 2
	                                        break

				        except:
				                traceback.print_exc()
                				sys.exit(1)

                                else:
                                        print "New host doesn't seem booted yet. Sleeping and will try again in 20 secs..."
                                        time.sleep(20)
                                        continue


if __name__ == "__main__":
        main()
