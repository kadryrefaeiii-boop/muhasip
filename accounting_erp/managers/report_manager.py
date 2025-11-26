#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Report Manager
Enhanced reporting with custom report builder
"""

import logging
import os
import pandas as pd
from datetime import datetime, date
from typing import Dict, Any, Optional, List
import json
from pathlib import Path

logger = logging.getLogger(__name__)

class ReportManager:
    """Enhanced reporting with custom report builder"""

    def __init__(self, db_manager):
        """
        Initialize Report Manager

        Args:
            db_manager: Database manager instance
        """
        self.db_manager = db_manager
        self.export_dir = "exports"
        self.template_dir = "templates"

        # Ensure directories exist
        os.makedirs(self.export_dir, exist_ok=True)
        os.makedirs(self.template_dir, exist_ok=True)

        logger.info("Report Manager initialized")

    def get_ledger(self, account_id: int, start_date: Optional[date] = None,
                   end_date: Optional[date] = None, filters: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """
        Get general ledger for account

        Args:
            account_id: Account ID
            start_date: Start date filter
            end_date: End date filter
            filters: Additional filters

        Returns:
            List of ledger transactions
        """
        try:
            # Get account information
            account = self.db_manager.get_record_by_id("accounts", account_id)
            if not account:
                logger.error(f"Account not found: {account_id}")
                return []

            # Build query
            query = """
                SELECT
                    je.entry_number,
                    je.date,
                    je.description as entry_description,
                    jl.description as line_description,
                    jl.debit,
                    jl.credit,
                    je.status,
                    je.created_at
                FROM journal_entries je
                JOIN journal_lines jl ON je.id = jl.entry_id
                WHERE jl.account_id = ? AND je.status = 'posted'
            """

            params = [account_id]

            if start_date:
                query += " AND je.date >= ?"
                params.append(start_date)

            if end_date:
                query += " AND je.date <= ?"
                params.append(end_date)

            query += " ORDER BY je.date, je.entry_number"

            # Execute query
            transactions = self.db_manager.execute_query(query, tuple(params), fetch_all=True)

            # Calculate running balance
            opening_balance = self.get_account_opening_balance(account_id, start_date)
            running_balance = opening_balance

            ledger_data = []
            for transaction in transactions or []:
                if transaction['debit'] > 0:
                    if account['account_category'] in ['asset', 'expense']:
                        running_balance += transaction['debit']
                    else:
                        running_balance -= transaction['debit']
                else:
                    if account['account_category'] in ['asset', 'expense']:
                        running_balance -= transaction['credit']
                    else:
                        running_balance += transaction['credit']

                ledger_data.append({
                    **transaction,
                    'running_balance': running_balance,
                    'account_code': account['code'],
                    'account_name': account['name_ar'],
                    'account_category': account['account_category']
                })

            # Add opening balance entry
            if opening_balance != 0:
                ledger_data.insert(0, {
                    'entry_number': None,
                    'date': start_date or account.get('created_at', datetime.now().date()),
                    'entry_description': 'Opening Balance',
                    'line_description': 'رصيد افتتاحي',
                    'debit': opening_balance if opening_balance > 0 else 0,
                    'credit': abs(opening_balance) if opening_balance < 0 else 0,
                    'running_balance': opening_balance,
                    'status': 'opening_balance',
                    'created_at': datetime.now()
                })

            return ledger_data

        except Exception as e:
            logger.error(f"Failed to get ledger: {e}")
            return []

    def get_account_opening_balance(self, account_id: int, as_of_date: Optional[date] = None) -> float:
        """Get opening balance for account as of date"""
        try:
            if not as_of_date:
                # Get account opening balance
                account = self.db_manager.get_record_by_id("accounts", account_id)
                return account.get('opening_balance', 0) if account else 0

            # Calculate balance from all transactions before date
            query = """
                SELECT
                    SUM(CASE WHEN debit > 0 THEN debit ELSE 0 END) as total_debit,
                    SUM(CASE WHEN credit > 0 THEN credit ELSE 0 END) as total_credit
                FROM journal_lines jl
                JOIN journal_entries je ON jl.entry_id = je.id
                WHERE jl.account_id = ? AND je.status = 'posted' AND je.date < ?
            """

            result = self.db_manager.execute_query(query, (account_id, as_of_date), fetch_one=True)

            if result:
                total_debit = result['total_debit'] or 0
                total_credit = result['total_credit'] or 0

                account = self.db_manager.get_record_by_id("accounts", account_id)
                if account and account['account_category'] in ['asset', 'expense']:
                    return account.get('opening_balance', 0) + total_debit - total_credit
                else:
                    return account.get('opening_balance', 0) - total_debit + total_credit

            return 0

        except Exception as e:
            logger.error(f"Failed to get opening balance: {e}")
            return 0

    def get_cost_accounts(self, start_date: Optional[date] = None,
                          end_date: Optional[date] = None) -> List[Dict[str, Any]]:
        """
        Get cost accounts report

        Args:
            start_date: Start date
            end_date: End date

        Returns:
            Cost accounts data
        """
        try:
            query = """
                SELECT
                    a.code,
                    a.name_ar,
                    a.name_en,
                    a.account_category,
                    SUM(CASE WHEN jl.debit > 0 THEN jl.debit ELSE 0 END) as total_debit,
                    SUM(CASE WHEN jl.credit > 0 THEN jl.credit ELSE 0 END) as total_credit,
                    a.opening_balance
                FROM accounts a
                LEFT JOIN journal_lines jl ON a.id = jl.account_id
                LEFT JOIN journal_entries je ON jl.entry_id = je.id
                    AND je.status = 'posted'
                WHERE a.account_category IN ('expense', 'revenue')
                AND a.is_active = 1
            """

            params = []
            if start_date:
                query += " AND (je.date IS NULL OR je.date >= ?)"
                params.append(start_date)

            if end_date:
                query += " AND (je.date IS NULL OR je.date <= ?)"
                params.append(end_date)

            query += " GROUP BY a.id, a.code, a.name_ar, a.name_en, a.account_category, a.opening_balance"
            query += " ORDER BY a.code"

            results = self.db_manager.execute_query(query, tuple(params), fetch_all=True)

            cost_data = []
            total_expenses = 0
            total_revenue = 0

            for row in results or []:
                opening_balance = row.get('opening_balance', 0)
                period_debit = row.get('total_debit', 0) or 0
                period_credit = row.get('total_credit', 0) or 0

                # Calculate net amount based on category
                if row['account_category'] == 'expense':
                    net_amount = opening_balance + period_debit - period_credit
                    total_expenses += net_amount
                else:  # revenue
                    net_amount = opening_balance - period_debit + period_credit
                    total_revenue += net_amount

                cost_data.append({
                    **row,
                    'opening_balance': opening_balance,
                    'period_debit': period_debit,
                    'period_credit': period_credit,
                    'net_amount': net_amount
                })

            # Add totals row
            cost_data.append({
                'code': None,
                'name_ar': 'الإجمالي / Total',
                'name_en': 'Total',
                'account_category': None,
                'opening_balance': 0,
                'total_debit': 0,
                'total_credit': 0,
                'net_amount': None
            })

            # Add net profit row
            net_profit = total_revenue - total_expenses
            cost_data.append({
                'code': None,
                'name_ar': 'صافي الربح / Net Profit',
                'name_en': 'Net Profit',
                'account_category': None,
                'opening_balance': 0,
                'total_debit': 0,
                'total_credit': 0,
                'net_amount': net_profit
            })

            return cost_data

        except Exception as e:
            logger.error(f"Failed to get cost accounts: {e}")
            return []

    def get_trial_balance(self, fiscal_year_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get trial balance

        Args:
            fiscal_year_id: Fiscal year ID (optional)

        Returns:
            Trial balance data
        """
        try:
            query = """
                SELECT
                    a.code,
                    a.name_ar,
                    a.name_en,
                    a.account_category,
                    a.opening_balance,
                    COALESCE(SUM(jl.debit), 0) as period_debit,
                    COALESCE(SUM(jl.credit), 0) as period_credit
                FROM accounts a
                LEFT JOIN journal_lines jl ON a.id = jl.account_id
                LEFT JOIN journal_entries je ON jl.entry_id = je.id
                    AND je.status = 'posted'
            """

            params = []
            if fiscal_year_id:
                query += " WHERE je.fiscal_year_id = ?"
                params.append(fiscal_year_id)

            query += " GROUP BY a.id, a.code, a.name_ar, a.name_en, a.account_category, a.opening_balance"
            query += " HAVING a.is_active = 1"
            query += " ORDER BY a.code"

            results = self.db_manager.execute_query(query, tuple(params), fetch_all=True)

            trial_balance = []
            total_debits = 0
            total_credits = 0

            for row in results or []:
                opening_balance = row.get('opening_balance', 0)
                period_debit = row.get('period_debit', 0) or 0
                period_credit = row.get('period_credit', 0) or 0

                # Calculate closing balance
                if row['account_category'] in ['asset', 'expense']:
                    closing_balance = opening_balance + period_debit - period_credit
                else:  # liability, revenue, equity
                    closing_balance = opening_balance - period_debit + period_credit

                # For trial balance, we need the debit/credit totals for balance sheet
                if closing_balance >= 0:
                    if row['account_category'] in ['asset', 'expense']:
                        trial_debit = closing_balance
                        trial_credit = 0
                    else:
                        trial_debit = 0
                        trial_credit = closing_balance
                else:
                    if row['account_category'] in ['asset', 'expense']:
                        trial_debit = 0
                        trial_credit = abs(closing_balance)
                    else:
                        trial_debit = abs(closing_balance)
                        trial_credit = 0

                total_debits += trial_debit
                total_credits += trial_credit

                trial_balance.append({
                    **row,
                    'opening_balance': opening_balance,
                    'period_debit': period_debit,
                    'period_credit': period_credit,
                    'closing_balance': closing_balance,
                    'trial_debit': trial_debit,
                    'trial_credit': trial_credit
                })

            # Add totals row
            trial_balance.append({
                'code': None,
                'name_ar': 'الإجمالي / Total',
                'name_en': 'Total',
                'account_category': None,
                'opening_balance': 0,
                'period_debit': 0,
                'period_credit': 0,
                'closing_balance': 0,
                'trial_debit': total_debits,
                'trial_credit': total_credits
            })

            return trial_balance

        except Exception as e:
            logger.error(f"Failed to get trial balance: {e}")
            return []

    def get_balance_sheet(self, as_of_date: date) -> Dict[str, Any]:
        """
        Get balance sheet as of specific date

        Args:
            as_of_date: Balance sheet date

        Returns:
            Balance sheet data
        """
        try:
            # Get trial balance up to date
            trial_balance = self.get_trial_balance(None)

            # Separate by category
            assets = []
            liabilities = []
            equity = []

            total_assets = 0
            total_liabilities = 0
            total_equity = 0

            for row in trial_balance:
                if row['code'] is None:  # Skip total row
                    continue

                category = row['account_category']
                balance = row['closing_balance']

                row_data = {
                    'code': row['code'],
                    'name_ar': row['name_ar'],
                    'name_en': row['name_en'],
                    'balance': balance
                }

                if category == 'asset':
                    assets.append(row_data)
                    total_assets += balance
                elif category == 'liability':
                    liabilities.append(row_data)
                    total_liabilities += balance
                elif category in ['equity', 'revenue', 'expense']:
                    equity.append(row_data)
                    # For balance sheet, revenue and expense affect equity
                    if category == 'revenue':
                        total_equity += balance
                    elif category == 'expense':
                        total_equity -= balance
                    else:  # equity
                        total_equity += balance

            return {
                'as_of_date': as_of_date,
                'assets': {
                    'accounts': assets,
                    'total': total_assets
                },
                'liabilities': {
                    'accounts': liabilities,
                    'total': total_liabilities
                },
                'equity': {
                    'accounts': equity,
                    'total': total_equity
                },
                'is_balanced': abs(total_assets - (total_liabilities + total_equity)) < 0.01
            }

        except Exception as e:
            logger.error(f"Failed to get balance sheet: {e}")
            return {}

    def get_income_statement(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """
        Get income statement for period

        Args:
            start_date: Period start date
            end_date: Period end date

        Returns:
            Income statement data
        """
        try:
            # Get revenue and expense accounts for period
            query = """
                SELECT
                    a.code,
                    a.name_ar,
                    a.name_en,
                    a.account_category,
                    COALESCE(SUM(jl.debit), 0) as total_debit,
                    COALESCE(SUM(jl.credit), 0) as total_credit,
                    a.opening_balance
                FROM accounts a
                LEFT JOIN journal_lines jl ON a.id = jl.account_id
                LEFT JOIN journal_entries je ON jl.entry_id = je.id
                    AND je.status = 'posted'
                WHERE a.account_category IN ('revenue', 'expense')
                AND a.is_active = 1
                AND je.date BETWEEN ? AND ?
                GROUP BY a.id, a.code, a.name_ar, a.name_en, a.account_category, a.opening_balance
                ORDER BY a.code
            """

            results = self.db_manager.execute_query(query, (start_date, end_date), fetch_all=True)

            revenues = []
            expenses = []
            total_revenue = 0
            total_expenses = 0

            for row in results or []:
                period_debit = row.get('total_debit', 0) or 0
                period_credit = row.get('total_credit', 0) or 0

                if row['account_category'] == 'revenue':
                    amount = period_credit - period_debit
                    revenues.append({
                        'code': row['code'],
                        'name_ar': row['name_ar'],
                        'name_en': row['name_en'],
                        'amount': amount
                    })
                    total_revenue += amount
                else:  # expense
                    amount = period_debit - period_credit
                    expenses.append({
                        'code': row['code'],
                        'name_ar': row['name_ar'],
                        'name_en': row['name_en'],
                        'amount': amount
                    })
                    total_expenses += amount

            # Calculate net income
            net_income = total_revenue - total_expenses

            return {
                'period_start': start_date,
                'period_end': end_date,
                'revenues': {
                    'accounts': revenues,
                    'total': total_revenue
                },
                'expenses': {
                    'accounts': expenses,
                    'total': total_expenses
                },
                'net_income': net_income,
                'gross_profit': total_revenue,  # Simplified
                'operating_income': net_income  # Simplified
            }

        except Exception as e:
            logger.error(f"Failed to get income statement: {e}")
            return {}

    def get_cash_flow(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """
        Get cash flow statement for period

        Args:
            start_date: Period start date
            end_date: Period end date

        Returns:
            Cash flow data
        """
        try:
            # Get cash and bank accounts
            query = """
                SELECT a.id, a.code, a.name_ar, a.name_en
                FROM accounts a
                WHERE (a.name_ar LIKE '%نقد%' OR a.name_ar LIKE '%بنك%' OR
                      a.name_en LIKE '%cash%' OR a.name_en LIKE '%bank%')
                AND a.is_active = 1
            """

            cash_accounts = self.db_manager.execute_query(query, fetch_all=True)

            cash_flows = {
                'operating': [],
                'investing': [],
                'financing': [],
                'net_change': 0,
                'beginning_balance': 0,
                'ending_balance': 0
            }

            total_cash_inflow = 0
            total_cash_outflow = 0

            # For each cash account, get transactions
            for account in cash_accounts or []:
                account_flows = self.get_ledger(account['id'], start_date, end_date)

                for flow in account_flows:
                    if flow['entry_number']:  # Skip opening balance
                        # Categorize cash flow (simplified)
                        category = self.categorize_cash_flow(flow)
                        cash_flows[category].append(flow)

                        if flow['debit'] > 0:
                            total_cash_outflow += flow['debit']
                        else:
                            total_cash_inflow += flow['credit']

            # Calculate totals
            cash_flows['net_change'] = total_cash_inflow - total_cash_outflow

            # Get beginning balance
            beginning_balance = 0
            for account in cash_accounts or []:
                balance = self.get_account_opening_balance(account['id'], start_date)
                beginning_balance += balance

            cash_flows['beginning_balance'] = beginning_balance
            cash_flows['ending_balance'] = beginning_balance + cash_flows['net_change']

            return cash_flows

        except Exception as e:
            logger.error(f"Failed to get cash flow: {e}")
            return {}

    def categorize_cash_flow(self, transaction: Dict[str, Any]) -> str:
        """Categorize cash flow transaction (simplified logic)"""
        try:
            description = f"{transaction.get('entry_description', '')} {transaction.get('line_description', '')}".lower()

            # Simple keyword-based categorization
            if any(keyword in description for keyword in ['salary', 'rent', 'utilities', 'supplies', 'operating']):
                return 'operating'
            elif any(keyword in description for keyword in ['equipment', 'building', 'machinery', 'investment']):
                return 'investing'
            elif any(keyword in description for keyword in ['loan', 'capital', 'shareholder', 'owner']):
                return 'financing'
            else:
                return 'operating'  # Default

        except Exception as e:
            logger.error(f"Failed to categorize cash flow: {e}")
            return 'operating'

    def export_to_excel(self, data: List[Dict[str, Any]], filename: str,
                        template: Optional[str] = None) -> Optional[str]:
        """
        Export data to Excel file

        Args:
            data: Data to export
            filename: Output filename
            template: Excel template to use

        Returns:
            Path to exported file
        """
        try:
            if not data:
                logger.error("No data to export")
                return None

            # Create DataFrame
            df = pd.DataFrame(data)

            # Generate output path
            if not filename.endswith('.xlsx'):
                filename += '.xlsx'
            output_path = os.path.join(self.export_dir, filename)

            # Export to Excel
            df.to_excel(output_path, index=False, engine='openpyxl')

            logger.info(f"Data exported to Excel: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Failed to export to Excel: {e}")
            return None

    def export_to_pdf(self, data: List[Dict[str, Any]], filename: str,
                     template: Optional[str] = None) -> Optional[str]:
        """
        Export data to PDF file

        Args:
            data: Data to export
            filename: Output filename
            template: PDF template to use

        Returns:
            Path to exported file
        """
        try:
            from reportlab.lib.pagesizes import letter, A4
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.lib import colors

            if not data:
                logger.error("No data to export")
                return None

            # Generate output path
            if not filename.endswith('.pdf'):
                filename += '.pdf'
            output_path = os.path.join(self.export_dir, filename)

            # Create PDF document
            doc = SimpleDocTemplate(output_path, pagesize=A4)
            styles = getSampleStyleSheet()

            # Prepare data for table
            if data:
                headers = list(data[0].keys())
                table_data = [headers]

                for row in data:
                    table_data.append([str(row.get(col, '')) for col in headers])

                # Create table
                table = Table(table_data)
                style = TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 14),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ])
                table.setStyle(style)

                # Build PDF
                elements = []
                elements.append(table)
                doc.build(elements)

            logger.info(f"Data exported to PDF: {output_path}")
            return output_path

        except ImportError:
            logger.error("ReportLab not available for PDF export")
            return None
        except Exception as e:
            logger.error(f"Failed to export to PDF: {e}")
            return None

    def create_custom_report(self, name: str, query: str, parameters: Dict[str, Any]) -> bool:
        """
        Create custom report

        Args:
            name: Report name
            query: SQL query
            parameters: Report parameters

        Returns:
            True if created successfully
        """
        try:
            report_data = {
                'name': name,
                'query': query,
                'parameters': json.dumps(parameters),
                'report_type': 'custom',
                'is_active': True,
                'created_by': getattr(self.db_manager, 'current_user_id', None)
            }

            report_id = self.db_manager.insert_record('reports', report_data)

            if report_id:
                logger.info(f"Custom report '{name}' created with ID: {report_id}")
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to create custom report: {e}")
            return False

    def get_report_list(self) -> List[Dict[str, Any]]:
        """Get list of available reports"""
        try:
            reports = self.db_manager.get_records('reports', where_clause='is_active = 1',
                                                   order_by='name')
            return reports

        except Exception as e:
            logger.error(f"Failed to get report list: {e}")
            return []

    def execute_report(self, report_id: int, parameters: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """
        Execute custom report

        Args:
            report_id: Report ID
            parameters: Report parameters

        Returns:
            Report results
        """
        try:
            # Get report definition
            report = self.db_manager.get_record_by_id('reports', report_id)
            if not report:
                logger.error(f"Report not found: {report_id}")
                return []

            # Parse query and parameters
            query = report['query']
            report_params = json.loads(report.get('parameters', '{}'))

            # Merge with runtime parameters
            if parameters:
                report_params.update(parameters)

            # Execute query with parameters
            if report_params:
                # Convert parameters dict to tuple in proper order
                param_values = tuple(report_params.values())
                results = self.db_manager.execute_query(query, param_values, fetch_all=True)
            else:
                results = self.db_manager.execute_query(query, fetch_all=True)

            return results or []

        except Exception as e:
            logger.error(f"Failed to execute report: {e}")
            return []

    def schedule_report(self, report_id: int, schedule: str, recipients: List[str]) -> bool:
        """
        Schedule report for automatic generation

        Args:
            report_id: Report ID
            schedule: Schedule string (cron format)
            recipients: List of email recipients

        Returns:
            True if scheduled successfully
        """
        try:
            # This would integrate with a task scheduler
            # For now, just store the schedule info
            schedule_data = {
                'report_id': report_id,
                'schedule': schedule,
                'recipients': recipients,
                'enabled': True
            }

            # Save to settings or dedicated table
            self.db_manager.insert_record('settings', {
                'key': f'report_schedule_{report_id}',
                'value': json.dumps(schedule_data),
                'data_type': 'json',
                'description': f'Scheduled report {report_id}'
            }, return_id=False)

            logger.info(f"Report {report_id} scheduled with schedule: {schedule}")
            return True

        except Exception as e:
            logger.error(f"Failed to schedule report: {e}")
            return False