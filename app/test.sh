#!/bin/bash


rm test.db && coverage run -m pytest
