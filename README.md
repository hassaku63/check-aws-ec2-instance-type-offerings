# README

Fetch AWS AZ data and instance type offerings. 

Use EC2 [DescribeInstanceTypeOfferings](https://docs.aws.amazon.com/ja_jp/AWSEC2/latest/APIReference/API_DescribeInstanceTypeOfferings.html) API and [DescribeAvailabilityZones](https://docs.aws.amazon.com/ja_jp/AWSEC2/latest/APIReference/API_DescribeAvailabilityZones.html) API.

## Usage

Fetch data to local db and quering.

### Fetch from AWS API

Set target region.

```bash
$ REGION=us-east-1
```

Fetch az data.

```bash
$ ./fetch_az_id_name_map.sh -h
Usage: fetch_az_id_name_map.sh -r <region> [-f <csv|tsv>]
  -a append header
  -r region
  -h help
```

```bash
$ AZ_FILE=az.tsv
$ ./fetch_az_id_name_map.sh -a -r ${REGION} > ${AZ_FILE}
```

Fetch instance type offerings.

```bash
$ ./list_ec2_instance_types_offering.sh -h
Usage: list_ec2_instance_types_offering.sh -r <region> [-f <csv|tsv>]
  -r region
  -h help
```

```bash
$ INSTANCE_TYPE_OFFERING_FILE=instance_type_offering.tsv
$ ./list_ec2_instance_types_offering.sh -r ${REGION} > ${INSTANCE_TYPE_OFFERING_FILE}
```

### Query

Created db has two tables.

```sql
# sqlite> .schema
CREATE TABLE az (
            ZoneId TEXT NOT NULL PRIMARY KEY,
            ZoneName TEXT NOT NULL,
            RegionName TEXT NOT NULL,
            ZoneType TEXT NOT NULL,
            State TEXT NOT NULL
        );
CREATE TABLE instance_type_offerings (
            InstanceType TEXT NOT NULL,
            LocationType TEXT NOT NULL,
            Location TEXT NOT NULL,
            PRIMARY KEY (Location, InstanceType)
        );
```

Example data is below.

```sql
sqlite> .headers ON
sqlite> .separator "\t"

sqlite> SELECT * FROM az;
-- ZoneId  ZoneName        RegionName      ZoneType        State
-- use1-az1        us-east-1a      us-east-1       availability-zone       available
-- use1-az2        us-east-1b      us-east-1       availability-zone       available
-- use1-az4        us-east-1c      us-east-1       availability-zone       available
-- use1-az6        us-east-1d      us-east-1       availability-zone       available
-- use1-az3        us-east-1e      us-east-1       availability-zone       available
-- use1-az5        us-east-1f      us-east-1       availability-zone       available

sqlite> SELECT * FROM instance_type_offerings LIMIT 5;
-- InstanceType    LocationType    Location
-- r7iz.large      region  us-east-1
-- inf2.8xlarge    region  us-east-1
-- r6a.32xlarge    region  us-east-1
-- c6i.4xlarge     region  us-east-1
-- x2iedn.24xlarge region  us-east-1

sqlite> SELECT * FROM instance_type_offerings WHERE LocationType = 'availability-zone-id' LIMIT 5;
-- InstanceType    LocationType    Location
-- c7gn.8xlarge    availability-zone-id    use1-az6
-- is4gen.xlarge   availability-zone-id    use1-az1
-- g5.4xlarge      availability-zone-id    use1-az4
-- m7i.metal-24xl  availability-zone-id    use1-az5
-- r5a.large       availability-zone-id    use1-az5
```

Cross join az and instance type offerings.

```sql
SELECT 
    it.InstanceType, 
    loc.Location, 
    CASE 
        WHEN it2.InstanceType IS NOT NULL THEN 1
        ELSE 0
    END as ExistsInLocation
FROM 
    (SELECT DISTINCT Location FROM instance_type_offerings WHERE LocationType = 'availability-zone-id') loc
CROSS JOIN 
    (SELECT DISTINCT InstanceType FROM instance_type_offerings WHERE LocationType = 'availability-zone-id') it
LEFT JOIN 
    instance_type_offerings it2 ON it.InstanceType = it2.InstanceType AND loc.Location = it2.Location
ORDER BY 
    loc.Location,
    it.InstanceType;
```

Output to tsv file.

```bash
$ sqlite3 -tabs -header instance_type_offerings.db << EOF > instance_type_offering_${REGION}.tsv
.headers ON
.separator "\t"
SELECT 
    it.InstanceType, 
    loc.Location, 
    CASE 
        WHEN it2.InstanceType IS NOT NULL THEN 1
        ELSE 0
    END as ExistsInLocation
FROM 
    (SELECT DISTINCT Location FROM instance_type_offerings WHERE LocationType = 'availability-zone-id') loc
CROSS JOIN 
    (SELECT DISTINCT InstanceType FROM instance_type_offerings WHERE LocationType = 'availability-zone-id') it
LEFT JOIN 
    instance_type_offerings it2 ON it.InstanceType = it2.InstanceType AND loc.Location = it2.Location
ORDER BY 
    loc.Location,
    it.InstanceType;
EOF
```

You can also output to markdown table. use `-markdown` option.

```bash
$ sqlite3 -markdown -header instance_type_offerings.db << EOF
SELECT 
    it.InstanceType, 
    loc.Location, 
    CASE 
        WHEN it2.InstanceType IS NOT NULL THEN 1
        ELSE 0
    END as ExistsInLocation
FROM 
    (SELECT DISTINCT Location FROM instance_type_offerings WHERE LocationType = 'availability-zone-id') loc
CROSS JOIN 
    (SELECT DISTINCT InstanceType FROM instance_type_offerings WHERE LocationType = 'availability-zone-id') it
LEFT JOIN 
    instance_type_offerings it2 ON it.InstanceType = it2.InstanceType AND loc.Location = it2.Location
ORDER BY 
    loc.Location,
    it.InstanceType;
EOF
# |   InstanceType    | Location | ExistsInLocation |
# |-------------------|----------|------------------|
# | a1.2xlarge        | use1-az1 | 0                |
# | a1.4xlarge        | use1-az1 | 0                |
# | a1.large          | use1-az1 | 0                |
# | a1.medium         | use1-az1 | 0                |
# | a1.metal          | use1-az1 | 0                |
# | a1.xlarge         | use1-az1 | 0                |
# | c1.medium         | use1-az1 | 1                |
# | c1.xlarge         | use1-az1 | 1                |
# ...
```

## Create materialized view

```sql
sqlite> CREATE VIEW IF NOT EXISTS exists_in_location_view AS
SELECT 
    it.InstanceType, 
    loc.Location, 
    CASE 
        WHEN it2.InstanceType IS NOT NULL THEN 1
        ELSE 0
    END as ExistsInLocation
FROM 
    (SELECT DISTINCT Location FROM instance_type_offerings WHERE LocationType = 'availability-zone-id') loc
CROSS JOIN 
    (SELECT DISTINCT InstanceType FROM instance_type_offerings WHERE LocationType = 'availability-zone-id') it
LEFT JOIN 
    instance_type_offerings it2 ON it.InstanceType = it2.InstanceType AND loc.Location = it2.Location
ORDER BY 
    loc.Location,
    it.InstanceType;
```

(Example query) Check t3 instance type offerings in use1-az3.

```sql
sqlite> .headers ON
sqlite> .separator "\t"
sqlite> SELECT Location, InstanceType, ExistsInLocation FROM temp.exists_in_location_view WHERE Location = 'use1-az3' and InstanceType LIKE 't3.%';
-- Location        InstanceType    ExistsInLocation
-- use1-az3        t3.2xlarge      0
-- use1-az3        t3.large        0
-- use1-az3        t3.medium       0
-- use1-az3        t3.micro        0
-- use1-az3        t3.nano 0
-- use1-az3        t3.small        0
-- use1-az3        t3.xlarge       0
```
