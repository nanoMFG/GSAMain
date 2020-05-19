import grp
groups = [grp.getgrgid(gid).gr_name for gid in os.getgroups()]

# Test for group membership
if '<some group>' in groups:
    DB_URL=''
    DB_USER='<read-write user>'
    DB_PASS='<read-write pass>'
    CA_CERT='<path-to-ca-cert>'
else:
    DB_URL=''
    DB_USER=''
    DB_PASS=''
    CA_CERT='<path-to-ca-cert>'

# Set config values for DEV TEST or PRODUCTION
DEV_DATABASE_URL='mysql+mysqlconnector://'+DB_USER+':'+DB_PASS+'@'+DB_URL
DEV_DATABASE_ARGS="{'ssl_ca':'"+CA_CERT+"'}"

