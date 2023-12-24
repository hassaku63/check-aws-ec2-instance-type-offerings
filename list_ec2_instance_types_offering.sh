#!/bin/bash

format=tsv
delimiter=
region=
append_header=0

function show_help() {
  echo "Usage: list_ec2_instance_types_offering.sh -r <region> [-f <csv|tsv>]"
  echo "  -r region"
  echo "  -a append header"
  echo "  -h help"
}

function list_enabled_regions() {
  aws account list-regions \
    --region-opt-status-contains ENABLED ENABLED_BY_DEFAULT \
    --query "Regions[].RegionName" \
    --output text
}

function set_delimiter() {
  if [ "$format" == "csv" ]; then
    delimiter=","
  elif [ "$format" == "tsv" ]; then
    delimiter="\t"
  fi
}

function main() {
  # show help if requested then exit
  if [ "$show_help" == "1" ]; then
    print_help
    exit 0
  fi

  set_delimiter

  # header
  if [ "$append_header" == "1" ]; then
    echo -e "InstanceType${delimiter}LocationType${delimiter}Location"
  fi

  for location_type in region availability-zone-id outpost; do
    arg_region=
    # set arg_region if region is set
    if [ ! -z "$region" ]; then
      arg_region=" --region $region "
    fi

    # >&2 echo "Getting instance types offering for location type: $location_type"

    if [ "$format" == "csv" ]; then
      aws ec2 ${arg_region} describe-instance-type-offerings --location-type ${location_type} \
      | jq -r '.InstanceTypeOfferings[] | [.InstanceType, .LocationType, .Location] | @csv'
    elif [ "$format" == "tsv" ]; then
      aws ec2 ${arg_region} describe-instance-type-offerings --location-type ${location_type} \
      | jq -r  '.InstanceTypeOfferings[] | [.InstanceType, .LocationType, .Location] | @tsv'
    fi
  done
}

while getopts "r:f:ah" opt; do
  case $opt in
    # a = appen header
    a)
      append_header=1
      ;;
    # r = region
    r)
      # check if region is valid
      available_regions=$(list_enabled_regions)
      if [[ ! $available_regions =~ (^|[[:space:]])$OPTARG($|[[:space:]]) ]]; then
        echo "Invalid region: $OPTARG" >&2
        # available regions to comma separated list
        echo "Available regions: $(echo $available_regions | tr '\n' ' ')" >&2
        exit 1
      fi
      region=$OPTARG
      ;;
    # f = format
    f)
      if [[ ! $OPTARG =~ ^(csv|tsv)$ ]]; then
        echo "Invalid format: $OPTARG" >&2
        exit 1
      fi
      format=$OPTARG
      ;;
    # help
    h)
      show_help
      exit 0
      ;;
    \?)
      echo "Invalid option: -$OPTARG" >&2
      exit 1
      ;;
  esac
  # if illegal option is passed, show help then exit
  if [ "$show_help" == "1" ]; then
    print_help
    exit 0
  fi
done

main "$@"