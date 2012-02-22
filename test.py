from libcloud.compute.types import Provider
from libcloud.compute.providers import get_driver
from libcloud.compute.ssh import SSHClient, ParamikoSSHClient
import libcloud.security
import os, sys, string, ConfigParser, socket, time, random, traceback
import fabric.api as fabric

libcloud.security.VERIFY_SSL_CERT = True


RACKSPACE_USER ='futuresoon'
RACKSPACE_KEY = '2b47b1319852c45553278e939fbac65b'

Driver = get_driver(Provider.RACKSPACE)
conn = Driver(RACKSPACE_USER, RACKSPACE_KEY)

# retrieve available images and sizes
images = conn.list_images()
print images
# [<NodeImage: id=3, name=Gentoo 2008.0, driver=Rackspace  ...>, ...]
sizes = conn.list_sizes()
print sizes
# [<NodeSize: id=1, name=256 server, ram=256 ... driver=Rackspace ...>, ...]

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

print config_distro
print config_size


#preferred_image = [image for image in images if config_distro in image.name]
#preferred_size = [size for size in sizes if config_size in size.name]

preferred_image = [image for image in images if config_distro in image.name]
preferred_size = [size for size in sizes if config_size in size.name]

print preferred_image
print preferred_size
