#!/usr/bin/env bash

BASE_URL="http://127.0.0.1:8000"

echo -e "Metoda\tŚcieżka\t\t\tOczekiwany\tOtrzymany\tStatus"
echo "------------------------------------------------------------------"

test_endpoint() {
  local method=$1
  local path=$2
  local expected=$3
  local data=$4

  if [ -n "$data" ]; then
    status=$(curl -s -o /dev/null -w "%{http_code}" -X "$method" "$BASE_URL$path" \
      -H "Content-Type: application/json" -d "$data")
  else
    status=$(curl -s -o /dev/null -w "%{http_code}" -X "$method" "$BASE_URL$path")
  fi

  if [ "$status" -eq "$expected" ]; then
    res="OK"
  else
    res="FAIL"
  fi

  printf "%-7s %-23s %-15s %-15s %s\n" "$method" "$path" "$expected" "$status" "$res"
}

test_endpoint "GET" "/projects" 200
test_endpoint "POST" "/projects" 201 '{"name": "Nowy Proj"}'
test_endpoint "POST" "/projects" 409 '{"name": "TaskBoard"}'
test_endpoint "GET" "/users" 200
test_endpoint "GET" "/tasks" 200
test_endpoint "POST" "/tasks" 422 '{"project_id": 999, "title": "Nie ma"}'
test_endpoint "DELETE" "/projects/1" 409