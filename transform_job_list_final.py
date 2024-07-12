import json
from jinja2 import Template



def main():

    data = {
        "tests": [
        {
            "name": "http_google",
            "type": "http",
            "spec": {
            "url": "www.google.com"
            }
        },
        {
            "name": "trace_google",
            "type": "trace",
            "spec": {
            "dest": "www.google.com"
            }
        },
        {
            "name": "rtt_google",
            "type": "rtt",
            "spec": {
            "dest": "www.google.com"
            }
        },
        {
            "name": "throughput_arbl",
            "type": "throughput",
            "spec": {
            "dest": "perfsonar-bin-arbl.umnet.umich.edu"
            }
        },
           {
            "name": "rtt_yahoo",
            "type": "rtt",
            "spec": {
            "dest": "www.yahoo.com"
            }
        }
        ],
        "jobs": [
        {
            "name": "job_http_google",
            "parallel": "True",
            "tests": [
            # "http_google",
            "rtt_google",
            #  "rtt_yahoo",
            "throughput_arbl",
            # "rtt_yahoo",
            "rtt_google",
            ],
            "continue-if": "true"
        },
        {
            "name": "job2",
            "parallel": "True",
            "tests": [
            "http_google",
            ],
            "continue-if": "true"
        },
        ],
        "batches": [
        {
            "name": "batch_http_google",
            "priority": 1,
            "test_interface": "wlan0",
            "ssid_profiles": [
            "Mwireless"
            ],
            "schedules": [
            "every_two_minutes",
            "every_three_minute"
            ],
            "jobs": [
            "job_http_google",
            "job2"
            ],
            "archivers": [
            "syslog"
            ]
        }
        ]
    }




    batch = {
        "name": "batch_http_google",
        "priority": 1,
        "test_interface": "wlan0",
        "ssid_profiles": [
          "Mwireless"
        ],
        "schedules": [
          
          "every_two_minutes",
          "every_three_minute"
        ],
        "jobs": [
          "job_http_google",
          "job2"
        ],
        "archivers": [
          "syslog"
        ]
      }
    


    template_str = """
    {
        "label": "{{ job_label }}",
        "iterations": {{ iteration }},
        "parallel": "{{ parallel }}",
        "backoff": "PT1S",
        "task": {
            "reference" : {
                "tasks" : [
                    {% for test in tests %}
                    {
                        "schema": 2,
                        "test": {
                            "type" : "{{ test.type }}",
                            "spec" : {
                                {% for key, value in test.spec.items() %}
                                    "{{ key }}": "{{ value }}"{% if not loop.last %},{% endif %}
                                {% endfor %}
                            }
                        },
                        "contexts": {
                            {% if test.type == 'throughput' %}
                                "schema": 1,
                                "contexts": [
                                    [
                                        {
                                            "context": "linuxnns",
                                            "data": {
                                                "namespace": "pssid"
                                            }
                                        }
                                    ],
                                    []
                                ]
                            {% else %}
                                "schema": 1,
                                "contexts": [
                                    [
                                        {
                                            "context": "linuxnns",
                                            "data": {
                                                "namespace": "pssid"
                                            }
                                        }
                                    ]
                                ]
                            {% endif %}
                        }
                    }{% if not loop.last %},{% endif %}
                    {% endfor %}
                ]
            }
        },
        "task-transform": {
            "script": [
                "# Replace the entire task section with one of the",
                "# tasks in the reference block based on the iteration.",
                ". = .reference.tasks[$iteration]"
            ]
        }
    }
    """
 
    transformed_job_list = []
   
    batch_tests = []

    # Iterate through each job in the batch
    for job_name in batch["jobs"]:
        # print("job_name -------------------------------------------------",job_name) 

        job = next((j for j in data['jobs'] if j['name'] == job_name), None)
        if job is None:
            # syslog.syslog(syslog.LOG_WARNING, f"Job '{job_name}' not found.")
            continue

        job_label = job['name']
        tests_list = job['tests']
        parallel = job['parallel']
        # parallel = bool(parallel)
        # print("type of parallel",type(parallel))
        # print("parallel",parallel)

        for test_name in tests_list:
            test = next((t for t in data['tests'] if t['name'] == test_name), None)
            
            if test is None:
                # syslog.syslog(syslog.LOG_WARNING, f"Test '{test_name}' not found.")
                continue
  
            batch_tests.append(test)

        template = Template(template_str)
        iteration = batch_tests.__len__()
        transformed_data_str = template.render(job_label=job_label, tests=batch_tests, iteration=iteration, parallel=parallel)
        # print("transformed_data_str",transformed_data_str)

        transformed_data = json.loads(transformed_data_str)
        transformed_job_list.append(transformed_data) 
       
   
    # Iterate through transformed_data in batch
    # for job in batch["transformed_data"]:
    for job in transformed_job_list:
        # Convert "parallel" from string to boolean if necessary
        if "parallel" in job:
            if job["parallel"] == "True":
                job["parallel"] = True
            elif job["parallel"] == "False":
                job["parallel"] = False
        
   
    print ("---- #### ----")
    batch.setdefault("batch_4_batchProcessor", []).extend(transformed_job_list)
    # print(batch)

    # if update boolean literals in above function, then below function is only for getting the batch for batch processor consumption
    batch_4_batchProcessor = {
    "schema": 3,
    "jobs": batch["batch_4_batchProcessor"]
    }

    print("---- **** ----")
    print(batch_4_batchProcessor)
    print(json.dumps(batch_4_batchProcessor, indent=4))



if __name__ == "__main__":
    main()


