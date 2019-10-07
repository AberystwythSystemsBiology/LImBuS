#!/bin/bash

function limbus-c() {
    docker-compose run web sh -c "find limbus -type f -name '*.pyc' -exec rm {} +"
}

function limbus-bwd() {
    limbus-b
    limbus-deps
}

function limbus-deps() {
    docker-compose run web sh -c "python3 -m venv venv && venv/bin/pip install -r requirements.txt && yarn install"
}

function limbus-b() {
    docker-compose build
}

function limbus-s() {
    docker-compose run --service-ports web sh -c "venv/bin/python limbus/run.py"
    limbus-c
}

function limbus-db-rebuild() {
      docker-compose run --service-ports web sh -c "rm -rf migrations"
      docker-compose run --service-ports web sh -c "venv/bin/flask db downgrade base"

      limbus-db-create
}


function limbus-db-create() {
    limbus-db-init
    limbus-db-migrate
    limbus-db-upgrade
}


function limbus-db-init() {
    docker-compose run web sh -c "venv/bin/flask db init"

}

function limbus-db-migrate() {
    docker-compose run web sh -c "venv/bin/flask db migrate"
}

function limbus-db-upgrade() {
    docker-compose run web sh -c "venv/bin/flask db upgrade"
}