#!/bin/sh
# INSTRUCTIONS (assumes debian-based distro)
# If you want something like this for OSX, check out the wiki page StartupOSX
# save to /etc/init.d/rssdler (NOT rssdler.sh!!)
# You must change user
# if you installed with setup.py
# and keep your config in ~/.rssdler/config.txt
# that is all you need to change here
# otherwise, edit  NAME, DAEMON, CONFIGFILE to suit needs
# chmod 755 /etc/init.d/rssdler
# sudo chown root:root /etc/init.d/rssdler
# sudo update-rc.d rssdler defaults

########
#BEGIN CONFIG
########
# user to run RSSDler as
user='user'
#where is the config file found
CONFIGFILE="`su -c 'echo $HOME' $user`/.rssdler/config.txt"
# name you saved RSSDler to
NAME='rssdler'
#directory you put rssdler, plus $NAME is the name of it
DAEMON="$NAME"
# options to pass to RSSDler
DAEMON_ARGS="-d -c '$CONFIGFILE'"
#where to log errors from this script
logfile="/var/log/rssdler.log"
########
#END CONFIG
########

WORKINGDIR=`cat "$CONFIGFILE" | grep -i "^workingDir" | sed -r "s/^workingDir\s*=\s*(.*)/\1/i"`
if [ -z $WORKINGDIR ] ; then
  WORKINGDIR="`su -c 'echo $HOME' $user`/.rssdler/"
fi
PIDFILE=`cat "$CONFIGFILE" | grep -i "^daemonInfo" | sed -r "s/^daemonInfo\s*=\s*(.*)/\1/i"`
if [ -z $PIDFILE ] ; then
  PIDFILE="$WORKINGDIR/daemon.info"
fi
PATH=/usr/bin:/usr/local/bin:/usr/local/sbin:/sbin:/bin:/usr/sbin
DESC="RSSDler"
SCRIPTNAME=/etc/init.d/rssdler

# Exit if the package is not installed
cd / # make sure we aren't looking at rssdler init script
exists=0
if ! [ -x "$DAEMON" ]  ; then
for i in `echo "$PATH" | tr ':' '\n'` ; do
    if [ -f $i/$DAEMON ] ; then
        exists=1
#   DAEMON=$i/$DAEMON
        break
    fi
done
if [ $exists -eq 0 ] ; then
    echo "cannot find daemon $DAEMON in PATH $PATH" | tee -a "$logfile" >&2
    exit 3
fi
fi

if [ -z $PIDFILE ] ; then
    echo "you didn't specify daemonInfo in your config file, nor is it where I expect"  | tee -a "$logfile" >&2
    exit 1
fi

if [ -z $WORKINGDIR ] ; then
    echo "you didn't specify a workingDir in your config file"  | tee -a "$logfile" >&2
    exit 1
fi

if ! [ -d "$WORKINGDIR" ] ; then
    echo "the workingDir you specified does not exist"  | tee -a "$logfile" >&2
    exit 1
fi

cd "$WORKINGDIR"

# Load the VERBOSE setting and other rcS variables
#. /lib/init/vars.sh

# Define LSB log_* functions.
# Depend on lsb-base (>= 3.0-6) to ensure that this file is present.
#. /lib/lsb/init-functions

do_start()  {
    if su -c "$DAEMON -s -c $CONFIGFILE > /dev/null 2>&1" $user; then
        echo "already running" | tee -a "$logfile" >&2
        return 1 # daemon already running
    fi 
    su -c "$DAEMON $DAEMON_ARGS" $user || return 2
}

do_stop()
{ # don't run as root so that PIDFILE is always writable by user
    su -c "$DAEMON -k -c '$CONFIGFILE'" $user || return 2 
}

cd "$WORKINGDIR"

case "$1" in
  start)
    echo "Starting $DESC: $NAME" | tee -a "$logfile"
    do_start
    echo "."
    ;;
  stop)
    echo "Stopping $DESC: $NAME" | tee -a "$logfile" 
    do_stop
    echo "."
    ;;
  restart|force-reload)
    echo "Restarting $DESC: $NAME" | tee -a "$logfile" 
    do_stop
    case "$?" in
      0|1)
        do_start
        ;;
    esac
    echo "."
    ;;
  *)
    echo "Usage: $SCRIPTNAME {start|stop|restart|force-reload}" >&2
    exit 3
    ;;
esac
