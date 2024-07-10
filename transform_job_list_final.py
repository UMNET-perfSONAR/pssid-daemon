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
            "name": "throughput_yahoo",
            "type": "throughput",
            "spec": {
            "dest": "www.yahoo.com"
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
            # "trace_google",
            # "throughput_yahoo",
            "rtt_yahoo",
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
            "job_http_google"
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
          "job_http_google"
        ],
        "archivers": [
          "syslog"
        ]
      }
    
    template_str_for_throughput = """
    {
        "label": "{{job_label}}",
        "iterations": {{iteration}},
        "parallel": "False",
        "backoff": "PT1M",
        "task": {
            "reference" : {
                "tasks" : [
                    {
                        "schema": 2,
                        "test": {
                            "name" : "{{test.name}}",
                            "type" : "{{test.type}}",
                            "spec" : {
                                {% for key, value in test.spec.items() %}
                                    "{{ key }}": "{{ value }}"{% if not loop.last %},{% endif %}
                                {% endfor %}
                            }
                        },
                        "contexts": {
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
                            ],
                            "schema": 1
                        }
                    }
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
    # template_str_for_non_throughput = """
    # {
    #     "label": "111",
    #     "iterations": 1111,
    #     "parallel": True,
    #     "backoff": "PT1M",
    #     "task": {
    #         "reference": {
    #             "tasks": [
    #                 {% for test_name in tests %}
    #                 {% set test = tests_dict[test_name] %}
    #                 {
    #                     "name": "{{ test.name }}",
    #                     "type": "{{ test.type }}",

    #                     "spec": {
    #                         {% for key, value in test.spec.items() %}
    #                         "{{ key }}": "{{ value }}"{% if not loop.last %},{% endif %}
    #                         {% endfor %}
    #                     }
    #                 }{% if not loop.last %},{% endif %}
    #                 {% endfor %}
    #             ]
    #         },
    #         "#": "This is intentionally empty:",
    #     },
    #     "task-transform": {
    #         "script": [
	#             "# Replace the entire task section with one of the",
	#             "# tasks in the reference block based on the iteration.",
	#             ". = .reference.tasks[$iteration]"
	#         ]
    #     }
    # }
    # """
    
    ##### compare the one below for debugging purpose
    # template_str_for_non_throughput = """
    # {
    #     "label": "{{job_label}}",
    #     "iterations": "{{iteration}}",
    #     "parallel": "{{parallel}}",
    #     "backoff": "PT1M",
    #     "task": {
    #         "reference" : {
    #            "tasks" : [
    #                 {% for test in tests %}
    #                 {
    #                     "schema": 2,
    #                     "test": {
                        
    #                         "name" : "{{test.name}}",
    #                         "type" : "{{test.type}}",
    #                         "spec" : {
    #                             {% for key, value in test.spec.items() %}
    #                                 "{{ key }}": "{{ value }}"{% if not loop.last %},{% endif %}
    #                             {% endfor %}
    #                         }
    #                     },
    #                     "contexts": {
    #                         "contexts": [
    #                             [
    #                             {
    #                                 "context": "linuxnns",
    #                                 "data": {
    #                                     "namespace": "pssid"
    #                                 }
    #                             }
    #                             ]
    #                         ],
    #                         "schema": 1
    #                     }
    #                 }{% if not loop.last %},{% endif %}
    # #               {% endfor %}
    #             ]
    #         }
    #     },
    #     "task-transform": {
    #         "script": [
	#             "# Replace the entire task section with one of the",
	#             "# tasks in the reference block based on the iteration.",
	#             ". = .reference.tasks[$iteration]"
	#         ]
    #     }
    # }
    # """

    template_str_for_non_throughput = """
{
    "label": "{{job_label}}",
    "iterations": {{iteration}},
    "parallel": "{{parallel}}",
    "backoff": "PT1S",
    "task": {
        "reference" : {
            "tasks" : [
                {% for test in tests %}
                {
                    "schema": 2,
                    "test": {
                        "type" : "{{test.type}}",
                        "spec" : {
                            {% for key, value in test.spec.items() %}
                                "{{ key }}": "{{ value }}"{% if not loop.last %},{% endif %}
                            {% endfor %}
                        }
                    },
                    "contexts": {
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
   
    non_throughput_tests = []

    # Iterate through each job in the batch
    for job_name in batch["jobs"]:
        job = next((j for j in data['jobs'] if j['name'] == job_name), None)
        if job is None:
            # syslog.syslog(syslog.LOG_WARNING, f"Job '{job_name}' not found.")
            continue

        job_label = job['name']
        tests_list = job['tests']
        parallel = job['parallel']
        # parallel = bool(parallel)
        print("type of parallel",type(parallel))
        print("parallel",parallel)

        for test_name in tests_list:
            test = next((t for t in data['tests'] if t['name'] == test_name), None)
            
            # tests_dict = {test_name : test}
            if test is None:
                # syslog.syslog(syslog.LOG_WARNING, f"Test '{test_name}' not found.")
                continue

            if test['type'] == 'throughput':
                template =  Template(template_str_for_throughput)
                iteration = 1
                transformed_data_str = template.render(job_label=job_label, test=test, iteration=iteration, parallel=parallel)
                transformed_data = json.loads(transformed_data_str)
                transformed_job_list.append(transformed_data)
                


            else:
                non_throughput_tests.append(test)
                

        if non_throughput_tests:
            # template = Template(template_str_for_non_throughput)
            # iteration = non_throughput_tests.__len__()
            # transformed_data_str = template.render(job_label=job_label, tests=non_throughput_tests, iteration=iteration, parallel=parallel)
            # # print('this is the transformed_data_str')
            # # print(transformed_data_str)
            # transformed_data = json.loads(transformed_data_str)
            # # print('this is the transformed_data, suposed to be a dictionary')
            # # print(transformed_data)
            # transformed_job_list.append(transformed_data)

            template = Template(template_str_for_non_throughput)
            iteration = non_throughput_tests.__len__()
            transformed_data_str = template.render(job_label=job_label, tests=non_throughput_tests, iteration=iteration, parallel=parallel)
            # print(transformed_data_str)
            transformed_data = json.loads(transformed_data_str)
            # formatted_json_str = json.dumps(transformed_data, indent=4)

            transformed_job_list.append(transformed_data) 
       
            # print(transformed_job_list)

    # print(json.dumps(transformed_job_list, indent=2))


        # Add transformed_job_list to batch under transformed_data
    batch.setdefault("transformed_data", []).extend(transformed_job_list)

    # Print or use batch dictionary with transformed_data added
    # print(json.dumps(batch, indent=2))

    # Create a new batch object with transformed_data inserted after jobs
    # new_batch = {
    #     "schema": 3,
    #     "jobs": batch["transformed_data"],
        
    # }
    # print('this is the new batch')

    
    # Print or use new_batch object
    # print(json.dumps(new_batch, indent=2))

    



    new_batch = {
    "schema": 3,
    "jobs": []
    }

    # Iterate through transformed_data in batch
    for job in batch["transformed_data"]:
        # Convert "parallel" from string to boolean if necessary
        if "parallel" in job:
            if job["parallel"] == "True":
                job["parallel"] = True
            elif job["parallel"] == "False":
                job["parallel"] = False
        
        # Append the processed job to new_batch["jobs"]
        new_batch["jobs"].append(job)


    print('this is the new batch')
    print(new_batch)
    print(json.dumps(new_batch, indent=4))



if __name__ == "__main__":
    main()


