# VPN Troubleshooting Runbook

## Authentication failed for several users
1. Check whether the failures started at the same time. A shared start time points to a server-side cause, not user error.
2. Review VPN gateway authentication logs for the affected users and source IP range.
3. Check for expired certificates or a recent password-policy change. Certificate expiry is the most common cause of mass failures.
4. Check the directory service (Active Directory or Entra ID) for locked accounts or sync problems.
5. Test a connection from a known-good device to confirm the gateway itself works.

## Single user cannot connect
Reset the user's VPN profile, confirm the account is not locked, and check that the device clock is correct.
