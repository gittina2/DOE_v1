import argparse
import sys
from typing import List, Optional
from doe.design_generation import generate_design
from doe.result_input import insert_results
from doe.analysis_computation import analyze_experiment
from doe.report_generation import generate_report
from doe.imports import parse_factors_csv, map_rows_to_factors, import_results_from_csv
from doe.experiment_creation import create_experiment
from doe.models import Response, DoeError, design
from doe.models.workflow_state import WorkflowState


def parse_response_arg(resp_str: str) -> Response:
    parts = resp_str.split(":")
    if len(parts) == 1:
        return Response(name=parts[0].strip(), type="continuous")
    elif len(parts) == 2:
        return Response(name=parts[0].strip(), type=parts[1].strip())  # type: ignore
    elif len(parts) >= 3:
        return Response(
            name=parts[0].strip(),
            type=parts[1].strip(),  # type: ignore
            unit=parts[2].strip() or None,
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

        new_state = generate_design(workflow_state, design_type=args.design_type)

        new_state.save_to_json(args.output)

        print(f"Design successfully generated and saved to {args.output}")

        return 0

    except DoeError as e:
        print(f"Workflow Error: {str(e)}", file=sys.stderr)
        return 1

    except Exception as e:
        print(f"System Error: {str(e)}", file=sys.stderr)
        return 1


def handle_insert_results(args) -> int:
    try:
        state_path = args.input if hasattr(args, "input") and args.input else getattr(args, "state", None)
        workflow_state = WorkflowState.load_from_json(state_path)
        responses = workflow_state.experiment.responses if workflow_state.experiment else None

        result_entries = import_results_from_csv(args.csv, design=workflow_state.design, responses=responses)

        new_state = insert_results(workflow_state, result_entries)

        output_path = args.output if args.output else state_path
        new_state.save_to_json(output_path)

        print(f"Results successfully inserted and saved to {output_path}")
        return 0

    except DoeError as e:
        print(f"Workflow Error: {str(e)}", file=sys.stderr)
        return 1

    except Exception as e:
        print(f"System Error: {str(e)}", file=sys.stderr)
        return 1


def handle_analyze(args) -> int:
    try:
        state_path = args.state if getattr(args, "state", None) else args.input
        workflow_state = WorkflowState.load_from_json(state_path)

        model_type = getattr(args, "model_type", "linear")
        new_state = analyze_experiment(workflow_state, model_type=model_type)

        output_path = args.output if args.output else state_path
        new_state.save_to_json(output_path)

        print(f"Analysis successfully computed and saved to {output_path}")
        return 0

    except DoeError as e:
        print(f"Workflow Error: {str(e)}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"System Error: {str(e)}", file=sys.stderr)
        return 1


def handle_report(args) -> int:
    try:
        state_path = args.state if getattr(args, "state", None) else args.input
        workflow_state = WorkflowState.load_from_json(state_path)

        out_path = args.output if getattr(args, "output", None) else getattr(args, "out", None)
        new_state = generate_report(workflow_state, output_path=out_path, format=args.format)

        if getattr(args, "state_output", None):
            new_state.save_to_json(args.state_output)

        print(f"Report successfully generated and saved to {out_path}")
        return 0

    except DoeError as e:
        print(f"Workflow Error: {str(e)}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"System Error: {str(e)}", file=sys.stderr)
        return 1


def handle_status(args) -> int:
    try:
        state_path = args.state if getattr(args, "state", None) else args.input
        workflow_state = WorkflowState.load_from_json(state_path)

        exp_name = workflow_state.experiment.name if workflow_state.experiment else "None"
        design_runs = len(workflow_state.design.runs) if workflow_state.design else "None"
        results_comp = workflow_state.results.completeness if workflow_state.results else "None"
        analysis_stat = "Created" if workflow_state.analysis else "None"

        print("Workflow Status Summary")
        print(f"  Step: {workflow_state.step}")
        print(f"  Schema Version: {workflow_state.schema_version}")
        print(f"  Experiment: {exp_name}")
        print(f"  Design Runs: {design_runs}")
        print(f"  Results Status: {results_comp}")
        print(f"  Analysis Status: {analysis_stat}")
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
    init_parser.add_argument(
        "--response",
        action="append",
        required=True,
        help="Response definition in name:type[:unit] format",
    )
    init_parser.add_argument(
        "--description", default=None, help="Description of the experiment (optional)"
    )
    init_parser.add_argument("--output", required=True, help="Path to save the WorkflowState JSON file")

    # generate-design subcommand
    design_parser = subparsers.add_parser(
        "generate-design", help="Generate a design for an existing experiment"
    )
    design_parser.add_argument(
        "--state",
        "--input", 
        dest="input",
        required=True, 
        help="Path to the input WorkflowState JSON file"
    )
    design_parser.add_argument(
        "--design-type",
        default="full_factorial",
        choices=["full_factorial", "fractional_factorial"],
        help="Design type (default: full_factorial)",
    )
    design_parser.add_argument(
        "--output", required=True, help="Path to save the updated WorkflowState JSON file"
    )

    # insert-results subcommand
    results_parser = subparsers.add_parser(
        "insert-results", help="Import and insert experimental results into WorkflowState"
    )
    results_parser.add_argument(
        "--state",
        "--input",
        dest="input",
        required=True,
        help="Path to the WorkflowState JSON file",
    )
    results_parser.add_argument("--csv", required=True, help="Path to the results CSV file")
    results_parser.add_argument(
        "--output",
        default=None,
        help="Path to save updated WorkflowState JSON file (defaults to overwriting --state)",
    )

    # analyze subcommand
    analyze_parser = subparsers.add_parser(
        "analyze", help="Run statistical analysis on complete results"
    )
    analyze_parser.add_argument(
        "--state",
        "--input",
        dest="state",
        required=True,
        help="Path to the WorkflowState JSON file",
    )
    analyze_parser.add_argument(
        "--model-type",
        default="linear",
        choices=["linear", "interaction", "quadratic"],
        help="Statistical model type (default: linear)",
    )
    analyze_parser.add_argument(
        "--output",
        default=None,
        help="Path to save updated WorkflowState JSON file (defaults to overwriting state)",
    )

    # report subcommand
    report_parser = subparsers.add_parser("report", help="Generate publication-ready report")
    report_parser.add_argument(
        "--state",
        "--input",
        dest="state",
        required=True,
        help="Path to the WorkflowState JSON file",
    )
    report_parser.add_argument(
        "--output",
        "--out",
        dest="output",
        required=True,
        help="Path to save the generated report file",
    )
    report_parser.add_argument(
        "--format",
        default="markdown",
        choices=["markdown"],
        help="Report format (default: markdown)",
    )
    report_parser.add_argument(
        "--state-output", default=None, help="Optional path to save updated WorkflowState JSON file"
    )

    # status subcommand
    status_parser = subparsers.add_parser("status", help="Display workflow state status summary")
    status_parser.add_argument(
        "--state",
        "--input",
        dest="state",
        required=True,
        help="Path to the WorkflowState JSON file",
    )

    args = parser.parse_args(argv)

    if args.command == "init-experiment":
        sys.exit(handle_init_experiment(args))
    elif args.command == "generate-design":
        sys.exit(handle_generate_design(args))
    elif args.command == "insert-results":
        sys.exit(handle_insert_results(args))
    elif args.command == "analyze":
        sys.exit(handle_analyze(args))
    elif args.command == "report":
        sys.exit(handle_report(args))
    elif args.command == "status":
        sys.exit(handle_status(args))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
