"""
Main module for the admin dashboard application.
"""
import reflex as rx

class DashboardState(rx.State):
    """State for the dashboard."""
    
    counter: int = 3
    
    def increment(self):
        """Increment the counter."""
        self.counter += 1
        
    def decrement(self):
        """Decrement the counter."""
        if self.counter > 0:
            self.counter -= 1

def index():
    """Main dashboard page."""
    return rx.center(
        rx.vstack(
            rx.heading("Catch Me If U Can - Admin Dashboard", size="3"),
            rx.text("Monitor workspace for inappropriate behavior, theft, and offensive language"),
            rx.divider(),
            
            rx.heading(f"Sample Dashboard", size="4"),
            rx.text("This is a simplified version of the dashboard."),
            rx.text("Current count: "),
            rx.heading(DashboardState.counter, size="4"),
            
            rx.hstack(
                rx.button(
                    "Decrement",
                    on_click=DashboardState.decrement,
                    color_scheme="red",
                ),
                rx.button(
                    "Increment",
                    on_click=DashboardState.increment,
                    color_scheme="green",
                ),
            ),
            
            width="800px",
            padding="20px",
            spacing="4",
        )
    )

# Create the app
app = rx.App()
app.add_page(index, route="/") 