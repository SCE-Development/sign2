#!/bin/sh

set -x
# get Core-v4 ip from config.json
CORE_V4_IP=$(cat /app/config/config.json | jq -r ".HEALTH_CHECK.CORE_V4_IP") 

# known_hosts remembers servers we've ssh'd into in the past.
# ssh can use this file to verify the legitimacy of CORE_V4_IP.
# So, we know for sure that we're setting up a connection to Core-v4
DOCKER_CONTAINER_KNOWN_HOSTS=/app/known_hosts

# This is sign2's private ssh key. It's needed in order to connect
# to Core-v4. Without this, ssh cannot decrypt data coming from
# Core-v4
DOCKER_CONTAINER_SSH_KEYS=/app/ssh_key

# This is the port on Core-v4 that will be forwarded into the conn
# container (try curl localhost:CORE_V4_PORT in Core-v4). Software responisble
# to check health checks, on Core-v4 will communicate with the container
# through Core-v4's localhost:CORE_V4_PORT.
CORE_V4_PORT=12121 

# This port is where sign2 should report health checks. Through this port,
# sign2 has a connection to Core-v4. Typically, sign2 will only be sending data
# out to Core-v4. 
SIGN2_PORT=8080

# intermediate variable to feed ssh command. It will look like sce@XXX.XXX.XXX.XXX
CORE_V4_HOST=sce@${CORE_V4_IP}

# Start the tunnel!
open_ssh_tunnel () {
    # (more info about the switches can be found in "man ssh")
    # -o is for option to give known_hosts
    # -i is for giving sign2's private key
    # -f -N makes ssh run in the background. We don't need a shell because
    #   we are just creating a tunnel.
    # -R is to port forward. This is actually what creates the tunnel! 
    #   This forwards packets created in Core-v4 and sent into its 
    #   localhost:CORE_V4_PORT to sign2's localhost:SIGN2_PORT and vise-versa.
    #   Consequently, this creates the tunnel from Core-v4:CORE_V4_PORT to
    #   sign2:SIGN2_PORT
    # Lastly, CORE_V4_HOST is given to signify the user and ip of Core-v4.

    ssh \
    -o UserKnownHostsFile=${DOCKER_CONTAINER_KNOWN_HOSTS} \
    -o StrictHostKeyChecking=no \
    -i ${DOCKER_CONTAINER_SSH_KEYS} \
    -f -g -N -R 0.0.0.0:${CORE_V4_PORT}:localhost:${SIGN2_PORT} ${CORE_V4_HOST}
}

# Change file permissions of the private key.
# 600 means only the owner should be able to read/write the file.
# If the permissions aren't tight, ssh complains and doesn't connect. 
chmod 600 ${DOCKER_CONTAINER_SSH_KEYS}


# if the first argument passed to the script, is --tunnel-only,
# we just open the ssh tunnel. i.e.
#
# $ ./what.sh --tunnel-only
# 
# to open the tunnel and start the server:
# $ ./tun.sh <args we want to send to the python server>
#
# the above args are passed to the python script with the $@ variable,
# for more info on $@, see https://stackoverflow.com/a/3811369
if [ "$1" = "--tunnel-only" ]
then
    open_ssh_tunnel
else
    open_ssh_tunnel
    python3 /app/server.py --config /app/server_config.yml $@
fi
