#!/usr/bin/env python3
"""Regenerate snapshots without altering live email copy or campaign history."""
from build_full_campaign import main as export_json
from generate_outreach import export_to_csv
from build_dashboard import build_dashboard


def main():
    export_json()
    export_to_csv()
    build_dashboard()


if __name__=='__main__': main()
