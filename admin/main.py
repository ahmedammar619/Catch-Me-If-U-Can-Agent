import reflex as rx
import os
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path to import from shared
sys.path.append(str(Path(__file__).parent.parent))
from shared.config import BASE_DIR

# Import AlertManager to access alerts
sys.path.append(str(BASE_DIR / "backend" / "agent"))
from utils.alert_manager import AlertManager

class AlertState(rx.State):
    """State for the alert dashboard."""
    
    # List of alerts
    alerts = []
    
    # Selected alert for details view
    selected_alert_id: str = None
    
    # Filter states
    filter_type: str = "all"
    filter_date: str = None  # ISO format date string
    show_false_positives: bool = True
    
    def on_mount(self):
        """Load alerts when the component mounts"""
        self.refresh_alerts()
    
    def get_filtered_alerts(self):
        """Get filtered alerts based on current filters."""
        # Load alerts from AlertManager
        alert_manager = AlertManager()
        all_alerts = alert_manager.get_all_alerts()
        
        # Apply filters
        filtered = []
        for alert in all_alerts:
            # Skip false positives if not showing them
            if not self.show_false_positives and alert["is_false_positive"]:
                continue
                
            # Filter by type
            if self.filter_type != "all" and alert["alert_type"] != self.filter_type:
                continue
                
            # Filter by date if set
            if self.filter_date:
                alert_date = alert["timestamp"].split("T")[0]
                if alert_date != self.filter_date:
                    continue
                    
            filtered.append(alert)
            
        return filtered
        
    def get_selected_alert(self):
        """Get the currently selected alert details."""
        if not self.selected_alert_id:
            return None
            
        alert_manager = AlertManager()
        return alert_manager.get_alert_by_id(self.selected_alert_id)
        
    def select_alert(self, alert_id: str):
        """Select an alert for detailed view."""
        self.selected_alert_id = alert_id
        
    def mark_as_false_positive(self, alert_id: str, feedback: str):
        """Mark an alert as a false positive."""
        alert_manager = AlertManager()
        alert_manager.mark_as_false_positive(alert_id, feedback)
        self.selected_alert_id = None  # Clear selection
        self.refresh_alerts()
        
    def delete_alert(self, alert_id: str):
        """Delete an alert."""
        alert_manager = AlertManager()
        alert_manager.delete_alert(alert_id)
        self.selected_alert_id = None  # Clear selection
        self.refresh_alerts()
        
    def refresh_alerts(self):
        """Refresh the alerts list."""
        self.alerts = self.get_filtered_alerts()
        
    def set_filter_type(self, alert_type: str):
        """Set the filter type."""
        self.filter_type = alert_type
        self.refresh_alerts()
        
    def set_filter_date(self, date: str):
        """Set the filter date."""
        self.filter_date = date
        self.refresh_alerts()
        
    def toggle_false_positives(self):
        """Toggle showing false positives."""
        self.show_false_positives = not self.show_false_positives
        self.refresh_alerts()


def alert_card(alert):
    """Create an alert card component."""
    icon = {
        "inappropriate_contact": "🤝", 
        "object_theft": "🔍",
        "offensive_language": "🗣️"
    }.get(alert["alert_type"], "⚠️")
    
    timestamp = datetime.fromisoformat(alert["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
    
    return rx.card(
        rx.hstack(
            rx.box(
                rx.heading(f"{icon} {alert['alert_type'].replace('_', ' ').title()}", size="4"),
                rx.text(f"Time: {timestamp}"),
                rx.text(alert["description"], font_style="italic", color="gray.600"),
                width="100%",
            ),
            rx.box(
                rx.cond(
                    alert["is_false_positive"],
                    rx.badge("False Positive", color_scheme="yellow"),
                    rx.badge("Alert", color_scheme="red"),
                ),
                padding="8px",
            ),
        ),
        rx.hstack(
            rx.button(
                "View Details",
                on_click=lambda: AlertState.select_alert(alert["id"]),
                color_scheme="blue",
                size="sm",
            ),
            justify="end",
            padding_top="8px",
        ),
        padding="12px",
        margin_bottom="12px",
        border_radius="md",
        border_width="1px",
        border_color="gray.200",
        on_click=lambda: AlertState.select_alert(alert["id"]),
        cursor="pointer",
        _hover={"shadow": "md"},
    )

def alert_details():
    """Create the alert details panel."""
    return rx.cond(
        AlertState.selected_alert_id,
        rx.box(
            rx.vstack(
                rx.heading("Alert Details", size="3"),
                rx.divider(),
                rx.hstack(
                    rx.vstack(
                        rx.heading(
                            lambda: f"{AlertState.get_selected_alert()['alert_type'].replace('_', ' ').title()}",
                            size="4",
                        ),
                        rx.text(
                            lambda: f"Time: {datetime.fromisoformat(AlertState.get_selected_alert()['timestamp']).strftime('%Y-%m-%d %H:%M:%S')}",
                        ),
                        rx.text(
                            lambda: AlertState.get_selected_alert()["description"],
                            font_style="italic",
                        ),
                        rx.cond(
                            lambda: AlertState.get_selected_alert()["is_false_positive"],
                            rx.vstack(
                                rx.badge("Marked as False Positive", color_scheme="yellow", size="md"),
                                rx.text(
                                    lambda: f"Feedback: {AlertState.get_selected_alert()['feedback']}", 
                                    color="gray.600",
                                ),
                            ),
                            rx.text(""),
                        ),
                        align_items="start",
                        width="100%",
                    ),
                ),
                rx.divider(),
                rx.cond(
                    lambda: AlertState.get_selected_alert()["video_path"],
                    rx.vstack(
                        rx.heading("Video Evidence", size="4"),
                        rx.html(
                            lambda: f"""
                            <div>Video evidence preview (static)</div>
                            """
                        ),
                        width="100%",
                    ),
                    rx.text("No video evidence available"),
                ),
                rx.cond(
                    lambda: AlertState.get_selected_alert()["audio_path"],
                    rx.vstack(
                        rx.heading("Audio Evidence", size="4"),
                        rx.html(
                            lambda: f"""
                            <div>Audio evidence preview (static)</div>
                            """
                        ),
                        width="100%",
                        padding_top="16px",
                    ),
                    rx.text("No audio evidence available"),
                ),
                rx.divider(),
                rx.hstack(
                    rx.button(
                        "Back to List",
                        on_click=lambda: AlertState.select_alert(None),
                        color_scheme="gray",
                    ),
                    rx.menu(
                        rx.menu_button("Actions", color_scheme="blue"),
                        rx.menu_list(
                            rx.cond(
                                lambda: not AlertState.get_selected_alert()["is_false_positive"],
                                rx.menu_item(
                                    "Mark as False Positive",
                                    on_click=rx.modal(
                                        rx.modal_overlay(
                                            rx.modal_content(
                                                rx.modal_header("Mark as False Positive"),
                                                rx.modal_body(
                                                    rx.form(
                                                        rx.vstack(
                                                            rx.text_area(
                                                                placeholder="Explain why this alert is a false positive",
                                                                id="feedback",
                                                            ),
                                                            rx.button(
                                                                "Submit",
                                                                type_="submit",
                                                                color_scheme="blue",
                                                            ),
                                                        ),
                                                        on_submit=lambda form_data: AlertState.mark_as_false_positive(
                                                            AlertState.selected_alert_id, form_data["feedback"]
                                                        ),
                                                    )
                                                ),
                                                rx.modal_footer(
                                                    rx.button(
                                                        "Cancel",
                                                        color_scheme="gray",
                                                        close_modal=True,
                                                    )
                                                ),
                                            )
                                        )
                                    ),
                                ),
                                rx.menu_item("Already Marked as False Positive", is_disabled=True),
                            ),
                            rx.menu_item(
                                "Delete Alert",
                                color_scheme="red",
                                on_click=rx.modal(
                                    rx.modal_overlay(
                                        rx.modal_content(
                                            rx.modal_header("Confirm Deletion"),
                                            rx.modal_body(
                                                "Are you sure you want to delete this alert? This action cannot be undone."
                                            ),
                                            rx.modal_footer(
                                                rx.hstack(
                                                    rx.button(
                                                        "Cancel",
                                                        color_scheme="gray",
                                                        close_modal=True,
                                                    ),
                                                    rx.button(
                                                        "Delete",
                                                        color_scheme="red",
                                                        on_click=lambda: AlertState.delete_alert(AlertState.selected_alert_id),
                                                        close_modal=True,
                                                    ),
                                                )
                                            ),
                                        )
                                    )
                                ),
                            ),
                        ),
                    ),
                    justify="space-between",
                    width="100%",
                ),
                spacing="16px",
                align_items="start",
                width="100%",
            ),
            padding="24px",
            border_radius="md",
            border_width="1px",
            border_color="gray.200",
            width="100%",
        ),
        rx.box(),  # Empty box when no alert is selected
    )

def index():
    """Main page of the dashboard."""
    return rx.center(
        # Main container with sidebar and content area
        rx.hstack(
            # Left sidebar
            rx.box(
        rx.vstack(
                    rx.heading("🕵️‍♂️ Catch Me If U Can - Admin Dashboard", size="3"),
                    rx.heading("Admin Dashboard", size="4", color="gray.600"),
            rx.divider(),
                    rx.heading("Filters", size="5", margin_top="20px"),
                    
                    # Filter by type
                rx.select(
                    ["all", "inappropriate_contact", "object_theft", "offensive_language"],
                    placeholder="Filter by type",
                    on_change=AlertState.set_filter_type,
                        default_value=AlertState.filter_type,
                ),
                    
                    # Filter by date
                rx.date_picker(
                    placeholder="Filter by date",
                    on_change=AlertState.set_filter_date,
                ),
                    
                    # Show/hide false positives
                rx.checkbox(
                        "Show false positives",
                        default_checked=AlertState.show_false_positives,
                    on_change=AlertState.toggle_false_positives,
                ),
                    
                    rx.button(
                        "Refresh Alerts",
                        on_click=AlertState.refresh_alerts,
                        color_scheme="blue",
                        margin_top="20px",
                    ),
                    height="100%",
                    align_items="start",
                    spacing="15px",
                    padding="20px",
                ),
                width="250px",
                height="100vh",
                border_right="1px solid #eaeaea",
            ),
            
            # Main content area
            rx.cond(
                AlertState.selected_alert_id,
                # Alert details view
                rx.box(
                alert_details(),
                    width="100%",
                    height="100vh",
                    padding="20px",
                    overflow_y="auto",
                ),
                # Alert list view
                rx.box(
                    rx.vstack(
                        rx.heading("Security Alerts", size="3"),
                        rx.text("Monitor and manage security incidents in the workspace"),
                        rx.divider(),
                        
                        # Alert list
                        rx.cond(
                            rx.len(AlertState.alerts) > 0,
                rx.vstack(
                    rx.foreach(
                                    AlertState.alerts,
                        alert_card,
                    ),
                                width="100%",
                    align_items="stretch",
                            ),
                            rx.box(
                                rx.center(
                                    rx.vstack(
                                        rx.icon("check_circle", size=32, color="green.500"),
                                        rx.text("No alerts found", font_size="xl", color="gray.500"),
                                        rx.text(
                                            "Your workspace is secure", 
                                            color="gray.500",
                                            margin_top="0",
                                        ),
                                    ),
                                    padding="100px",
                                ),
                                border="1px dashed #eaeaea",
                                border_radius="md",
                                margin_top="20px",
                            ),
                        ),
                        width="100%",
                        align_items="start",
                        padding="20px",
                    ),
                    width="100%",
                    height="100vh",
                    overflow_y="auto",
                ),
            ),
            width="100%",
            height="100vh",
            align_items="stretch",
        ),
            width="100%",
    )

# Create the app
app = rx.App()

# Add the index page
app.add_page(index, title="Catch Me If U Can - Admin Dashboard") 