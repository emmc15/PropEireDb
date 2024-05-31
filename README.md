# PropEireDb

Repo for <www.propeiredb.ie>, a dashboard that visualizes Irish Property Register Data

# Quickstart

1. git clone this repo
2. run `docker compose up` (this should autobuild if not already)
3. Launch interactive shell into the container`docker exec -it propeiredb bash`
    - `cd src`
    - `python3 cli.py run-pipeline`
    - Once finished exit shell
4. Comment out `entrypoint: sleep infinity` and uncomment `entrypoint: cd src && gunicorn wsgi:server -b 8000`
5. `docker compose down` to bring container down, `docker compose up` to launch website with pulled data

# TODO

- [X] set up geoncode api
- [ ] basic function to pull geoencode data
- [ ] add cli command
- [ ] Deploy
- [ ] Add cron
- [ ] Create proper restore function
