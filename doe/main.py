import argparse
import sys
from typing import List, Optional
from doe.design_generation import generate_design
from doe.result_input import insert_results
from doe.imports import parse_factors_csv, map_rows_to_factors, import_results_from_csv
from doe.experiment_creation import create_experiment
from doe.models import Response, DoeError
from doe.models.workflow_state import WorkflowState

def parse_response_arg(resp_str: str) -> Response:
    parts = resp_str.split(":")
    if len(parts) == 1:
        return Response(name=parts[0].strip(), type="continuous")
    elif len(parts) == 2:
        return Response(name=parts[0].strip(), type=parts[1].strip()) # type: ignore
    elif len(parts) >= 3:
        return Response(
            name=parts[0].strip(),
            type=parts[1].strip(), # type: ignore
            unit=parts[2].strip() or None
        )
    else:
        raise ValueError(
            f"Invalid response format: {resp_str}. Expected 'name:type' or 'name:type:unit'."
        )

def handle_init_experiment(args) -> int:
    try:
        # 1. Parse factors CSV
        parsed_rows = parse_factors_csv(args.factors_csv)
        factors = map_rows_to_factors(parsed_rows)
        
        # 2. Parse responses
        responses = []
        for resp_str in args.response:
            try:
                r = parse_response_arg(resp_str)
                responses.append(r)
            except Exception as e:
                print(f"Error parsing response '{resp_str}': {str(e)}", file=sys.stderr)
                return 1
                
        # 3. Create experiment and WorkflowState
        workflow_state = create_experiment(
            name=args.name,
            factors=factors,
            responses=responses,
            design_type=args.design_type,
            planned_runs=args.planned_runs,
            description=args.description,
        )
        
        # 4. Persist WorkflowState
        workflow_state.save_to_json(args.output)
        print(f"Experiment successfully created and saved to {args.output}")
        return 0
        
    except DoeError as e:
        print(f"Domain Validation/Workflow Error: {str(e)}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"System Error: {str(e)}", file=sys.stderr)
        return 1
    
def handle_generate_design(args) -> int:
    try:
        workflow_state = WorkflowState.load_from_json(args.input)

        new_state = generate_design(workflow_state)

        new_state.save_to_json(args.output)

        print(
            f"Design successfully generated and saved to {args.output}"
        )

        return 0

    except DoeError as e:
        print(f"Workflow Error: {str(e)}", file=sys.stderr)
        return 1

    except Exception as e:
        print(f"System Error: {str(e)}", file=sys.stderr)
        return 1

def handle_insert_results(args) -> int:
    try:
        workflow_state = WorkflowState.load_from_json(args.input)
        responses = workflow_state.experiment.responses if workflow_state.experiment else None
        result_entries = import_results_from_csv(args.csv, design=workflow_state.design, responses=responses)

        new_state = insert_results(workflow_state, result_entries)

        output_path = args.output if args.output else args.input
        new_state.save_to_json(output_path)

        print(f"Results successfully inserted and saved to {output_path}")
        return 0

    except DoeError as e:
        print(f"Workflow Error: {str(e)}", file=sys.stderr)
        return 1

    except Exception as e:
        print(f"System Error: {str(e)}", file=sys.stderr)
        return 1

def main(argv: Optional[List[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="DOE Python Core CLI Engine")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # init-experiment subcommand
    init_parser = subparsers.add_parser("init-experiment", help="Initialize a new experiment")
    init_parser.add_argument("--name", required=True, help="Name of the experiment")
    init_parser.add_argument("--factors-csv", required=True, help="Path to factors CSV file")
    init_parser.add_argument("--response", action="append", required=True, help="Response definition in name:type[:unit] format")
    init_parser.add_argument("--design-type", required=True, choices=["full_factorial", "fractional_factorial"], help="Design type")
    init_parser.add_argument("--planned-runs", type=int, default=None, help="Number of planned runs (optional)")
    init_parser.add_argument("--description", default=None, help="Description of the experiment (optional)")
    init_parser.add_argument("--output", required=True, help="Path to save the WorkflowState JSON file")
    
    # generate-design subcommand
    design_parser = subparsers.add_parser("generate-design", help="Generate a design for an existing experiment")
    design_parser.add_argument("--input", required=True, help="Path to the input WorkflowState JSON file")
    design_parser.add_argument("--output", required=True, help="Path to save the updated WorkflowState JSON file")

    # insert-results subcommand
    results_parser = subparsers.add_parser("insert-results", help="Import and insert experimental results into WorkflowState")
    results_parser.add_argument("--input", required=True, help="Path to the WorkflowState JSON file")
    results_parser.add_argument("--csv", required=True, help="Path to the results CSV file")
    results_parser.add_argument("--output", default=None, help="Path to save updated WorkflowState JSON file (defaults to overwriting --state)")

    args = parser.parse_args(argv)
    
    if args.command == "init-experiment":
        sys.exit(handle_init_experiment(args))
    elif args.command == "generate-design":
        sys.exit(handle_generate_design(args))
    elif args.command == "insert-results":
        sys.exit(handle_insert_results(args))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
