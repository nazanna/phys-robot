#!/bin/bash
yc config profile create my-robot-profile
yc config set service-account-key ./secrets/authorized_key.json
yc config set cloud-id b1gvlkoml0iiqe48ta64
yc config set folder-id b1gj7jpn68t36v7gjhu2

