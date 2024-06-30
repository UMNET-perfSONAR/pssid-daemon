import json
from jinja2 import Template



# with open('template.j2', 'r') as template_file:
#     template_content = template_file.read()

def main():

    data = {
        'jobs': [
            {
                'name': 'job1',
                'tests': [
                    {
                        'type': 'test_type1',
                        'spec': {
                            'param1': 'value1',
                            'param2': 'value2'
                        }
                    },
                    {
                        'type': 'test_type2',
                        'spec': {
                            'param3': 'value3',
                            'param4': 'value4',
                            'param5': 'value5',
                        }
                    }
                ]
            },
                        {
                'name': 'job2',
                'tests': [
                    {
                        'type': 'test_type2',
                        'spec': {
                            'paramA': 'valueA',
                            'paramB': 'valueB'
                        }
                    },
                    {
                        'type': 'test_type2',
                        'spec': {
                            'paramC': 'valueC',
                            'paramD': 'valueD',
                            'paramE': 'valueE',
                        }
                    }
                ]
            }
        ]
    }

    with open('template.j2', 'r') as template_file:
        template_str = template_file.read()
        # print("marker00")
        # print(template_str)

    print("marker")

    # template string sample in debug mode
    # template_str = """
    #     {
    #         "label": "{{ job_label }}",
    #         "iterations": 1,
    #         "parallel": true,
    #         "backoff": "PT1M",
    #         "task": {
    #             "reference": {
    #                 "tests": [
    #                     {% for test in tests %}
    #                     {
    #                         "type": "{{ test.type }}",
    #                         "spec": {
    #                             {% for key, value in test.spec.items() %}
    #                             "{{ key }}": "{{ value }}"{% if not loop.last %},{% endif %}
    #                             {% endfor %}
    #                         }
    #                     }{% if not loop.last %},{% endif %}
    #                     {% endfor %}
    #                 ]
    #             },
    #             "#": "This is intentionally empty:",
    #             "test": {}
    #         },
    #         "task-transform": {
    #             "script": [
    #                 "# Replace the test section of the task with one of the",
    #                 "# tests in the reference block based on the iteration.",
    #                 ".test = .reference.tests[$iteration]"
    #             ]
    #         }
    #     }

    # """

    template = Template(template_str)
    transformed_job_list = []

    # define the batch --> data
    batch = {
    'jobs': ['job1','job2']  
    }

    # Iterate through each job in the batch
    for job_name in batch["jobs"]:
        job = next((j for j in data['jobs'] if j['name'] == job_name), None)
        if job is None:
            # syslog.syslog(syslog.LOG_WARNING, f"Job '{job_name}' not found.")
            continue

        job_label = job['name']
        tests = job['tests']

        # Render the template with job-specific data
        transformed_data_str = template.render(job_label=job_label, tests=tests)
        print("marker2")
        transformed_data = json.loads(transformed_data_str)

        transformed_job_list.append(transformed_data)

    print(json.dumps(transformed_job_list, indent=2))

if __name__ == "__main__":
    main()