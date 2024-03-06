# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt


from hms.hms_module.report.hms_accounts_receivable_summary.hms_accounts_receivable_summary import (
	HMSAccountsReceivableSummary,
)


def execute(filters=None):
	args = {
		"account_type": "Payable",
		"naming_by": ["Buying Settings", "supp_master_name"],
	}
	return HMSAccountsReceivableSummary(filters).run(args)
