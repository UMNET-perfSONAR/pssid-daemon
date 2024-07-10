
import pscheduler.batchprocessor
import sys
from croniter import croniter

def debug(message):
    """
    Callback function for the batch processor to emit a line of
    debug.
    """
    print(message, file=sys.stderr)

def main():

    print("Hello World!")
    batch = {
        "schema": 3,
        "jobs": [
            {
                "label": "different-in-parallel",
                "iterations": 2,
                "parallel": True,
                "backoff": "PT1S",
                "task": {
                "reference": {
                    "tasks": [
                    {   
                        "schema": 2,
                        "test": {
                        "type": "rtt",
                        "spec": {
                            "dest": "perfsonar-bin-arbl.umnet.umich.edu"
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
                            ]
                        ],
                        "schema": 1
                        }
                    },
                    {   
                        "schema": 2,
                        "test": {
                        "type": "trace",
                        "spec": {
                            "dest": "perfsonar-bin-arbl.umnet.umich.edu"
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
                            ]
                        ],
                        "schema": 1
                        }
                    },
                    ]

                },
                "#": "This is intentionally empty.  Will be filled in by the transform.",
                },
                "task-transform": {
                "script": [
                    "# Replace the entire task section with one of the",
                    "# tasks in the reference block based on the iteration.",
                    ". = .reference.tasks[$iteration]"
                ]
                }
            },

            {
                "label": "different-in-parallel",
                "iterations": 2,
                "parallel": True,
                "backoff": "PT1S",
                "task": {
                "reference": {
                    "tasks": [
                    {   
                        "schema": 2,
                        "test": {
                        "type": "trace",
                        "spec": {
                            "dest": "perfsonar-bin-arbl.umnet.umich.edu"
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
                            ]
                        ],
                        "schema": 1
                        }
                    },
                    {   
                        "schema": 2,
                        "test": {
                        "type": "rtt",
                        "spec": {
                            "dest": "perfsonar-bin-arbl.umnet.umich.edu"
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
                            ]
                        ],
                        "schema": 1
                        }
                    },
                    ]

                },
                "#": "This is intentionally empty.  Will be filled in by the transform.",
                },
                "task-transform": {
                "script": [
                    "# Replace the entire task section with one of the",
                    "# tasks in the reference block based on the iteration.",
                    ". = .reference.tasks[$iteration]"
                ]
                }
            }
        ]
    }


    
    processor = pscheduler.batchprocessor.BatchProcessor(batch)
    result = processor(debug=debug)

if __name__ == "__main__":
    main()