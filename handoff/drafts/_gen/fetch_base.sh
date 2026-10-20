#!/bin/bash
# Fill ./base with the exact blobs of the base commit that the edit scripts start from.
# usage: REPO=D:/geometry-axiom BASE_REV=09ab5f79 ./fetch_base.sh
cd "$(dirname "$0")"
REPO="${REPO:-D:/geometry-axiom}"
REV="${BASE_REV:-09ab5f79}"
for f in \
  geometry-templates/woodworking/native/contacts.h \
  geometry-templates/woodworking/native/contacts.c \
  geometry-templates/woodworking/native/contact_world.h \
  geometry-templates/woodworking/native/contact_world.c \
  geometry-templates/woodworking/native/world_validation.c \
  tests/geo261_contacts_harness.c \
  tests/geo261_contact_world_harness.c \
  tests/geo261_host_facts_authority_harness.c \
  tests/test_geo261_wood_contacts.py \
  tests/test_geo261_wood_contact_world.py \
  tests/test_geo261_wood_world_validation.py \
  tests/run_tests.py \
  tests/mutate.py \
  tests/test_geo261_mutation_migration.py \
  tests/run_all.expected.json \
  geometry-core/domain-decoupling/product-architecture.json \
  geometry-core/references.inc \
  current_geometry.c ; do
  mkdir -p "base/$(dirname "$f")"
  git -C "$REPO" show "$REV:$f" > "base/$f" || { echo "missing $f at $REV"; exit 1; }
done
echo "base filled from $REV"
