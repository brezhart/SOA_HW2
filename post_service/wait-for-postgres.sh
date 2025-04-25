#!/bin/sh

set -e


host="$1"
port="$2"
shift 3
cmd="$@"

until PGPASSWORD=$POSTGRES_PASSWORD psql -h "$host" -U "user" -d "mydatabase" -c '\q'; do
  >&2 echo "Postgres is unavailable - sleeping" $host 
  sleep 1
done

>&2 echo "Postgres is up - executing command"
exec $cmd
