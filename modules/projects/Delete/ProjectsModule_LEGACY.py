

# PyQt5
from PyQt5.QtWidgets import (
    QLabel, QVBoxLayout, QScrollArea, QWidget, QFrame, QHBoxLayout
)
from PyQt5.QtCore import Qt

# Internal modules
from ....ui.ModuleBaseUI import ModuleBaseUI
from ....languages.language_manager import LanguageManager
from ....utils.api_client import APIClient
from ....utils.GraphQLQueryLoader import GraphQLQueryLoader


class ProjectHeaderFrame(QFrame):
    def __init__(self, project, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.NoFrame)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Left: Name and client info
        name_client_frame = QFrame()
        name_client_layout = QVBoxLayout(name_client_frame)
        name_client_layout.setContentsMargins(0, 0, 0, 0)

        # Name and number
        name = project.get('name', 'No Name')
        number = project.get('number', '-')
        name_label = QLabel(f"<b>{name}</b> <span class='project-number'>#{number}</span>")
        name_label.setTextFormat(Qt.RichText)
        name_label.setObjectName("ProjectNameLabel")
        name_client_layout.addWidget(name_label)
        # Client label
        client = project.get('client')
        if client:
            client_label = QLabel(f"<b>Klient:</b> <span class='client-name'>{client['displayName']}</span>")
            client_label.setTextFormat(Qt.RichText)
            client_label.setObjectName("ProjectClientLabel")
            name_client_layout.addWidget(client_label)
        name_client_frame.setLayout(name_client_layout)
        layout.addWidget(name_client_frame)

class ExtraInfoFrame(QFrame):
    def __init__(self, project, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.NoFrame)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        extra_info_widget = ExtraInfoWidget(project)
        layout.addWidget(extra_info_widget)

class ProjectMembersWidget(QWidget):
    def __init__(self, project, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        members = project.get('members', {}).get('edges', [])
        responsible_list = []
        participants_list = []
        for m in members:
            node = m.get('node', {})
            name = node.get('displayName', '-')
            responsible = m.get('isResponsible')
            deleted = node.get('deletedAt')
            classes = []
            if responsible:
                classes.append('responsible')
            if deleted:
                classes.append('deleted')
            class_str = ' '.join(classes)
            if responsible:
                responsible_list.append(f"<span class='{class_str}'>{name}</span>")
            else:
                participants_list.append(f"<span class='{class_str}'>{name}</span>")
        resp_label = QLabel(f"<b>Vastutaja:</b> {', '.join(responsible_list) if responsible_list else '-'}")
        resp_label.setTextFormat(Qt.RichText)
        resp_label.setObjectName("ProjectResponsibleLabel")
        part_label = QLabel(f"<b>Osalejad:</b> {', '.join(participants_list) if participants_list else '-'}")
        part_label.setTextFormat(Qt.RichText)
        part_label.setObjectName("ProjectParticipantsLabel")
        layout.addWidget(resp_label)
        layout.addWidget(part_label)

class ExtraInfoWidget(QWidget):
    def __init__(self, project, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        # Placeholder for future data
        label = QLabel("<i>Lisaandmed tulevad siia...</i>")
        label.setTextFormat(Qt.RichText)
        layout.addWidget(label)

class StatusWidget(QWidget):
    # List of possible status names for width calculation
    STATUS_NAMES = [
        "Uus", "Töös", "Lõpetatud", "Ootel", "Katkestatud", "Tagasi lükatud", "Kinnitatud", "Tühistatud", "Arhiveeritud"
    ]
    def __init__(self, project, theme, parent=None):
        super().__init__(parent)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        # Public/Private
        if not project.get('isPublic'):
            pub_label = QLabel("!")
            pub_label.setObjectName("ProjectPrivateIcon")
            row.addWidget(pub_label)
        # Status
        status = project.get('status', {})
        status_name = status.get('name', '-')
        status_color = status.get('color', 'cccccc')
        status_label = QLabel(status_name)
        status_label.setAlignment(Qt.AlignCenter)
        status_label.setFixedWidth(100)
        status_label.setObjectName("ProjectStatusLabel")
        # Theming for status badge is now handled in project_card.qss using objectName and dynamic property
        status_label.setProperty("statusColor", status_color)
        row.addWidget(status_label)
        row.addStretch(1)
        main_layout.addLayout(row)
        # Dates below status
        dates_widget = DatesWidget(project)
        main_layout.addWidget(dates_widget)
class DatesWidget(QWidget):
    def __init__(self, project, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        def format_date(label, value, due=False):
            if not value:
                return f"<b>{label}:</b> -"
            try:
                dt = datetime.datetime.fromisoformat(value)
                today = datetime.datetime.now().date()
                date_str = dt.strftime('%d.%m.%Y')
                style = ""
                if due:
                    days_left = (dt.date() - today).days
                    if days_left < 0:
                        style = "color:#e53935;font-weight:bold;"  # Red for overdue
                    elif days_left <= 3:
                        style = "color:#ff9800;font-weight:bold;"  # Orange for due soon
                return f"<b>{label}:</b> <span style='{style}'>{date_str}</span>"
            except Exception:
                return f"<b>{label}:</b> {value}"

        date_items = [
            ("Algus", project.get('startAt'), False),
            ("Tähtaeg", project.get('dueAt'), True),
            ("Loodud", project.get('createdAt'), False),
            ("Muudetud", project.get('updatedAt'), False),
        ]
        for label, value, due in date_items:
            lbl = QLabel(format_date(label, value, due))
            lbl.setTextFormat(Qt.RichText)
            layout.addWidget(lbl)
        layout.addStretch(1)


class ProjectsModule_LEGACY(ModuleBaseUI):

    def on_theme_toggled(self):
        """
        Call this method after ThemeManager.toggle_theme(...) is used.
        It will restyle all project cards to match the new theme.
        """
        self.restyle_project_cards()
        # Example usage (in your theme toggle handler):
        # ThemeManager.toggle_theme(...)
        # projects_module.on_theme_toggled()

    @staticmethod
    def restyle_project_cards_static(feed_layout):
        """Re-apply the current theme to all visible project cards (static version)."""
        try:
            from ....widgets.theme_manager import ThemeManager
            from ....constants.file_paths import StylePaths
            theme = ThemeManager.load_theme_setting()
            theme_dir = StylePaths.DARK if theme == "dark" else StylePaths.LIGHT
            for i in range(feed_layout.count()):
                widget = feed_layout.itemAt(i).widget()
                if isinstance(widget, QFrame) and widget.objectName() == "ModuleInfoCard":
                    ThemeManager.apply_theme(widget, theme_dir, ["project_card.qss"])
        except Exception:
            pass

    def restyle_project_cards(self):
        """Re-apply the current theme to all visible project cards (instance version)."""
        self.restyle_project_cards_static(self.feed_layout)
    name = "ProjectsModule"

    @classmethod
    def get_widget(cls, *args, **kwargs):
        return cls(*args, **kwargs)

    def __init__(self, lang_manager=None, theme_manager=None, theme_dir=None, qss_files=None, parent=None):
        super().__init__(parent)
        self.lang_manager = lang_manager or LanguageManager()
        self.theme_manager = theme_manager
        self.theme_dir = theme_dir
        self.qss_files = qss_files or []
        if self.theme_manager and self.theme_dir and self.qss_files:
            self.theme_manager.apply_theme(self, self.theme_dir, self.qss_files)

        # Ensure display_area has a layout
        if not self.display_area.layout():
            self.display_area.setLayout(QVBoxLayout())

        # Remove placeholder label
        for i in reversed(range(self.display_area.layout().count())):
            widget = self.display_area.layout().itemAt(i).widget()
            if widget:
                widget.setParent(None)

        # Set up scroll area for project feed
        from PyQt5.QtWidgets import QSizePolicy
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.feed_content = QWidget()
        self.feed_layout = QVBoxLayout()
        self.feed_content.setLayout(self.feed_layout)
        # Set size policy and minimum size for feed_content
        self.feed_content.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.feed_content.setMinimumHeight(200)
        self.feed_content.setMinimumWidth(200)
        self.scroll_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.scroll_area.setMinimumHeight(200)
        self.scroll_area.setMinimumWidth(200)
        self.scroll_area.setWidget(self.feed_content)
        self.display_area.layout().addWidget(self.scroll_area)

        # API and query setup
        self.api_client = APIClient(self.lang_manager)
        self.query_loader = GraphQLQueryLoader(self.lang_manager)
        self.query = self.query_loader.load_query("PROJECT", "ListAllProjects.graphql")
        # Pagination state
        self.projects_end_cursor = None
        self.has_more = True
        self.is_loading = False
        self.batch_size = 5
        self.fetched_projects = []

        # Connect scroll event
        self.scroll_area.verticalScrollBar().valueChanged.connect(self.on_scroll)

        # Only load projects when module is activated
        self._activated = False

    def load_next_batch(self):
        if self.is_loading or not self.has_more:
            print("[ProjectsModule] Skipping load: is_loading=", self.is_loading, "has_more=", self.has_more)
            return
        self.is_loading = True
        variables = {
            "first": self.batch_size,
            "after": self.projects_end_cursor,
            # No restrictions: do not set where/search/orderBy/trashed unless needed
        }
        try:
            data = self.api_client.send_query(self.query, variables)
            print("[ProjectsModule] Received data from API:", data)
            projects = data.get("projects", {}).get("edges", [])
            print(f"[ProjectsModule] Number of projects fetched: {len(projects)}")
            page_info = data.get("projects", {}).get("pageInfo", {})
            self.projects_end_cursor = page_info.get("endCursor")
            self.has_more = page_info.get("hasNextPage", False)
            self.add_projects_to_feed([edge["node"] for edge in projects])
        except Exception as e:
            import traceback
            import sys
            tb = traceback.format_exc()
            print(f"[ProjectsModule] GraphQL error: {e}\n{tb}", file=sys.stderr)
            self.feed_layout.addWidget(QLabel(f"GraphQL error: {e}"))
        self.is_loading = False

    def add_projects_to_feed(self, projects):
        print(f"[ProjectsModule] add_projects_to_feed called with {len(projects)} projects")
        for idx, project in enumerate(projects):
            print(f"[ProjectsModule] Creating card for project {idx}: {project.get('name', '-')} (calling create_project_card)")
            card = self.create_project_card(project)
            print(f"[ProjectsModule] Adding card widget: {card}")
            self.feed_layout.addWidget(card)
        print(f"[ProjectsModule] feed_layout count after add: {self.feed_layout.count()}")
        self.feed_content.updateGeometry()
        self.feed_content.adjustSize()
        self.feed_content.show()
        self.scroll_area.updateGeometry()
        self.scroll_area.adjustSize()
        self.scroll_area.show()
        self.display_area.updateGeometry()
        self.display_area.adjustSize()
        self.display_area.show()
        self.fetched_projects.extend(projects)


    def create_project_card(self, project):
        print(f"[ProjectsModule] create_project_card called for project: {project.get('name', '-')} (start)")
        card = QFrame()
        card.setFrameShape(QFrame.StyledPanel)
        card.setObjectName("ModuleInfoCard")

        # Use ThemeManager to apply the correct QSS for the card (dynamic, theme-aware)
        try:
            from ....widgets.theme_manager import ThemeManager
            from ....constants.file_paths import StylePaths
            theme = ThemeManager.load_theme_setting()
            theme_dir = StylePaths.DARK if theme == "dark" else StylePaths.LIGHT
            ThemeManager.apply_theme(card, theme_dir, ["project_card.qss"])
            print(f"[ProjectsModule] Theme applied to card for project: {project.get('name', '-')} (theme: {theme})")
        except Exception as e:
            print(f"[ProjectsModule] ThemeManager.apply_theme failed: {e}")

        # Main card layout: horizontal (content left, status right)
        main_layout = QHBoxLayout(card)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Left: Inner frame holding header+members+extra data (vertical)
        content_frame = QFrame()
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(0, 0, 0, 0)

        # Header and members row
        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 0)
        header_frame = ProjectHeaderFrame(project)
        print(f"[ProjectsModule] ProjectHeaderFrame created for project: {project.get('name', '-')}")
        header_row.addWidget(header_frame, alignment=Qt.AlignTop)
        header_row.addStretch(1)
        members_widget = ProjectMembersWidget(project)
        print(f"[ProjectsModule] ProjectMembersWidget created for project: {project.get('name', '-')}")
        header_row.addWidget(members_widget, alignment=Qt.AlignRight | Qt.AlignTop)
        content_layout.addLayout(header_row)

        # Extra info frame below
        extra_info_frame = ExtraInfoFrame(project)
        print(f"[ProjectsModule] ExtraInfoFrame created for project: {project.get('name', '-')}")
        content_layout.addWidget(extra_info_frame)

        main_layout.addWidget(content_frame)

        # Right: Status widget (top aligned)
        status_widget = StatusWidget(project, theme)
        print(f"[ProjectsModule] StatusWidget created for project: {project.get('name', '-')}")
        status_col = QVBoxLayout()
        status_col.setContentsMargins(0, 0, 0, 0)
        status_col.addWidget(status_widget, alignment=Qt.AlignTop | Qt.AlignRight)
        status_col.addStretch(1)
        main_layout.addLayout(status_col)

        print(f"[ProjectsModule] create_project_card finished for project: {project.get('name', '-')}")
        return card

    def on_scroll(self, value):
        bar = self.scroll_area.verticalScrollBar()
        if value == bar.maximum() and self.has_more and not self.is_loading:
            self.load_next_batch()

    def activate(self):
        """Activate the module."""
        print("[ProjectsModule] activate() called")
        if not self._activated:
            print("[ProjectsModule] Activating and loading next batch...")
            self._activated = True
            self.load_next_batch()
        else:
            print("[ProjectsModule] Already activated.")

    @staticmethod
    def deactivate():
        """Deactivate the module."""
        pass

