#!/usr/bin/env python3
"""Legacy notification command delegates to configured private mobile channels."""
import sys
from notify_mobile import notify_user_mobile
from generate_outreach import load_leads


def main():
    return notify_user_mobile('Outreach campaign',f'{len(load_leads())} leads recorded. Review the current campaign snapshot.')


if __name__=='__main__': sys.exit(0 if main() else 1)
