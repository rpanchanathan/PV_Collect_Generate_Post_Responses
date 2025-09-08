"""Email notification utilities for daily run summaries."""

import smtplib
import os
from datetime import datetime, timedelta
from typing import Dict, List
import logging

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)

class EmailNotifier:
    """Email notification service for daily run summaries."""
    
    def __init__(self):
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.sender_email = os.getenv('SENDER_EMAIL')
        self.sender_password = os.getenv('SENDER_PASSWORD')
        self.recipient_email = os.getenv('RECIPIENT_EMAIL', 'rajesh@genwise.in')
        
        if not all([self.sender_email, self.sender_password]):
            logger.warning("Email credentials not configured - notifications disabled")
    
    def send_daily_summary(self, run_summary: Dict) -> bool:
        """Send daily run summary email."""
        try:
            if not self.sender_email or not self.sender_password:
                logger.warning("Cannot send email - credentials not configured")
                return False
            
            # Create email content
            subject = self._generate_subject(run_summary)
            html_body = self._generate_html_body(run_summary)
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.sender_email
            msg['To'] = self.recipient_email
            
            # Attach HTML body
            html_part = MIMEText(html_body, 'html')
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
            
            logger.info(f"Daily summary email sent to {self.recipient_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False
    
    def _generate_subject(self, run_summary: Dict) -> str:
        """Generate email subject line."""
        recent_runs = run_summary.get('recent_runs', [])
        if not recent_runs:
            return "🔍 PV Reviews: No recent runs"
        
        latest_run = recent_runs[0]
        status = latest_run.get('status', 'Unknown')
        new_reviews = latest_run.get('new_reviews', 0)
        
        if status == 'SUCCESS':
            if new_reviews > 0:
                return f"✅ PV Reviews: {new_reviews} new reviews collected"
            else:
                return "✅ PV Reviews: No new reviews (all up to date)"
        else:
            return f"❌ PV Reviews: Collection failed - {status}"
    
    def _generate_html_body(self, run_summary: Dict) -> str:
        """Generate HTML email body."""
        recent_runs = run_summary.get('recent_runs', [])
        total_reviews = run_summary.get('total_reviews', 0)
        unreplied_reviews = run_summary.get('unreplied_reviews', 0)
        
        # Header
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px;">
                    🏮 Paati Veedu Reviews - Daily Summary
                </h2>
                
                <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="margin-top: 0; color: #495057;">📊 Overview</h3>
                    <ul style="list-style: none; padding: 0;">
                        <li style="margin: 8px 0;"><strong>Total Reviews:</strong> {total_reviews}</li>
                        <li style="margin: 8px 0;"><strong>Unreplied Reviews:</strong> {unreplied_reviews}</li>
                        <li style="margin: 8px 0;"><strong>Generated:</strong> {datetime.now().strftime('%B %d, %Y at %H:%M UTC')}</li>
                    </ul>
                </div>
        """
        
        # Latest Run Details
        if recent_runs:
            latest_run = recent_runs[0]
            status_color = "#28a745" if latest_run.get('status') == 'SUCCESS' else "#dc3545"
            status_icon = "✅" if latest_run.get('status') == 'SUCCESS' else "❌"
            
            html += f"""
                <div style="background: {status_color}15; border-left: 4px solid {status_color}; padding: 15px; margin: 20px 0;">
                    <h3 style="margin-top: 0; color: {status_color};">{status_icon} Latest Run</h3>
                    <ul style="list-style: none; padding: 0;">
                        <li style="margin: 8px 0;"><strong>Date:</strong> {latest_run.get('run_date', 'Unknown')}</li>
                        <li style="margin: 8px 0;"><strong>Status:</strong> {latest_run.get('status', 'Unknown')}</li>
                        <li style="margin: 8px 0;"><strong>Reviews Collected:</strong> {latest_run.get('reviews_collected', 0)}</li>
                        <li style="margin: 8px 0;"><strong>New Reviews:</strong> {latest_run.get('new_reviews', 0)}</li>
                        <li style="margin: 8px 0;"><strong>Duration:</strong> {latest_run.get('duration_seconds', 0):.1f}s</li>
            """
            
            if latest_run.get('error_message'):
                html += f'<li style="margin: 8px 0; color: #dc3545;"><strong>Error:</strong> {latest_run.get("error_message")}</li>'
            
            html += "</ul></div>"
        
        # Recent Runs History
        if len(recent_runs) > 1:
            html += """
                <div style="margin: 20px 0;">
                    <h3 style="color: #495057;">📅 Recent Runs (Last 7 Days)</h3>
                    <table style="width: 100%; border-collapse: collapse; border: 1px solid #dee2e6;">
                        <thead>
                            <tr style="background: #f8f9fa;">
                                <th style="padding: 12px; text-align: left; border: 1px solid #dee2e6;">Date</th>
                                <th style="padding: 12px; text-align: left; border: 1px solid #dee2e6;">Status</th>
                                <th style="padding: 12px; text-align: left; border: 1px solid #dee2e6;">New Reviews</th>
                                <th style="padding: 12px; text-align: left; border: 1px solid #dee2e6;">Duration</th>
                            </tr>
                        </thead>
                        <tbody>
            """
            
            for run in recent_runs[:7]:  # Last 7 runs
                status_color = "#28a745" if run.get('status') == 'SUCCESS' else "#dc3545"
                html += f"""
                    <tr>
                        <td style="padding: 12px; border: 1px solid #dee2e6;">{run.get('run_date', 'Unknown')}</td>
                        <td style="padding: 12px; border: 1px solid #dee2e6; color: {status_color};">{run.get('status', 'Unknown')}</td>
                        <td style="padding: 12px; border: 1px solid #dee2e6;">{run.get('new_reviews', 0)}</td>
                        <td style="padding: 12px; border: 1px solid #dee2e6;">{run.get('duration_seconds', 0):.1f}s</td>
                    </tr>
                """
            
            html += "</tbody></table></div>"
        
        # Footer
        html += f"""
                <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #dee2e6; font-size: 0.9em; color: #6c757d;">
                    <p>This is an automated report from the PV Reviews collection system.</p>
                    <p><strong>Next scheduled run:</strong> {(datetime.now() + timedelta(days=1)).strftime('%B %d, %Y')}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html