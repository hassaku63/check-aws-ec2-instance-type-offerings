# README

Sample output for us-east-1 and ap-notheast-1.

[!NOTE]
> The data presented under the output/ directory are samples and current as of December 2023.


```bash
$ DB_FILE=instance_type_offerings.db

# us-east-1
$ sqlite3 ${DB_FILE} << EOF > output/us-east-1.tsv
.header ON
.separator "\t"
SELECT Location, InstanceType, ExistsInLocation FROM exists_in_location_view WHERE Location LIKE 'use1-%';
EOF

# ap-northeast-1
$ sqlite3 ${DB_FILE} << EOF > output/ap-northeast-1.tsv
.header ON
.separator "\t"
SELECT Location, InstanceType, ExistsInLocation FROM exists_in_location_view WHERE Location LIKE 'apne1-%';
EOF
```

## markdown output

### us-east-1

```bash
$ sqlite3 ${DB_FILE} -markdown << EOF >> output/README.md
SELECT InstanceType, Location, ExistsInLocation FROM exists_in_location_view WHERE Location LIKE 'use1-%' ORDER BY InstanceType, Location;
EOF
```

|   InstanceType    | Location | ExistsInLocation |
|-------------------|----------|------------------|
| a1.2xlarge        | use1-az1 | 0                |
| a1.2xlarge        | use1-az2 | 1                |
| a1.2xlarge        | use1-az3 | 0                |
| a1.2xlarge        | use1-az4 | 1                |
| a1.2xlarge        | use1-az5 | 0                |
| a1.2xlarge        | use1-az6 | 1                |
| a1.4xlarge        | use1-az1 | 0                |
| a1.4xlarge        | use1-az2 | 1                |
| ...               | ...      | 0                |

### ap-northeast-1

```bash
$ sqlite3 ${DB_FILE} -markdown << EOF >> output/README.md
SELECT InstanceType, Location, ExistsInLocation FROM exists_in_location_view WHERE Location LIKE 'use1-%' ORDER BY InstanceType, Location;
EOF
```

|   InstanceType    | Location  | ExistsInLocation |
|-------------------|-----------|------------------|
| a1.2xlarge        | apne1-az1 | 0                |
| a1.2xlarge        | apne1-az2 | 1                |
| a1.2xlarge        | apne1-az4 | 1                |
| a1.4xlarge        | apne1-az1 | 0                |
| a1.4xlarge        | apne1-az2 | 1                |
| ...               | ...       | 0                |

