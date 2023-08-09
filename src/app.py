import os
import configparser
from github import Github
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import re

class App:
    def __init__(self, root):
        self.root = root
        self.username = ""
        self.token = ""
        self.repository = ""
        self.title = ""
        self.branchPrepend = ""
        self.body = ""
        self.head = ""
        self.base = ""
        self.root.title("GitHub Pull Request App")
        self.github = ""

        # Read GitHub configuration from the configuration file
        self.username, self.token, self.repository, self.title, self.branchPrepend, self.body, self.head, self.base = self.read_config()
        self.github = Github(self.token)

        # Create the Notebook widget to hold multiple tabs
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Create Pull Request Tab
        self.pr_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.pr_tab, text="Create Pull Request")

        # Entry fields for Feature Flag Name and Feature Flag Value
        ttk.Label(self.pr_tab, text="Feature Flag Name:").grid(row=0, column=0)
        self.feature_flag_name_entry = ttk.Entry(self.pr_tab)
        self.feature_flag_name_entry.grid(row=0, column=1)

        ttk.Label(self.pr_tab, text="Feature Flag Value:").grid(row=1, column=0)
        self.feature_flag_value_entry = ttk.Entry(self.pr_tab)
        self.feature_flag_value_entry.grid(row=1, column=1)

        # Create button for updating feature flags
        self.update_flags_button = ttk.Button(self.pr_tab, text="Update Feature Flags", command=self.update_feature_flags)
        self.update_flags_button.grid(row=2, column=0, columnspan=2, pady=10)

        # Update Configuration Tab
        self.update_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.update_tab, text="Update Configuration")

        # Create labels and entry fields for GitHub configuration
        ttk.Label(self.update_tab, text="GitHub Username:").grid(row=0, column=0)
        self.username_entry = ttk.Entry(self.update_tab)
        self.username_entry.insert(0, self.username)  # Set the default value
        self.username_entry.grid(row=0, column=1)

        ttk.Label(self.update_tab, text="GitHub Token:").grid(row=1, column=0)
        self.token_entry = ttk.Entry(self.update_tab)
        self.token_entry.insert(0, self.token)  # Set the default value
        self.token_entry.grid(row=1, column=1)

        ttk.Label(self.update_tab, text="Repository:").grid(row=2, column=0)
        self.repository_entry = ttk.Entry(self.update_tab)
        self.repository_entry.insert(0, self.repository)  # Set the default value
        self.repository_entry.grid(row=2, column=1)

        ttk.Label(self.update_tab, text="Pull Request Title:").grid(row=3, column=0)
        self.title_entry = ttk.Entry(self.update_tab)
        self.title_entry.insert(0, self.title)  # Set the default value
        self.title_entry.grid(row=3, column=1)

        ttk.Label(self.update_tab, text="Pull Request Body:").grid(row=4, column=0)
        self.body_entry = tk.Text(self.update_tab, width=30, height=5)
        self.body_entry.insert('1.0', self.body)  # Set the default value
        self.body_entry.grid(row=4, column=1)

        ttk.Label(self.update_tab, text="Branch with Changes:").grid(row=5, column=0)
        self.head_entry = ttk.Entry(self.update_tab)
        self.head_entry.insert(0, self.head)  # Set the default value
        self.head_entry.grid(row=5, column=1)

        ttk.Label(self.update_tab, text="Desired Branch prepend (branch name will have the environment appended to the end):").grid(row=6, column=0)
        self.base_entry = ttk.Entry(self.update_tab)
        self.base_entry.insert(0, self.branchPrepend)  # Set the default value
        self.base_entry.grid(row=6, column=1)

        ttk.Label(self.update_tab, text="Base Branch:").grid(row=7, column=0)
        self.base_entry = ttk.Entry(self.update_tab)
        self.base_entry.insert(0, self.base)  # Set the default value
        self.base_entry.grid(row=7, column=1)

        # Create button for updating configuration
        self.update_config_button = ttk.Button(self.update_tab, text="Update Configuration", command=self.update_config)
        self.update_config_button.grid(row=8, column=0, columnspan=2, pady=10)
        
        # Create the subfolder selection checkboxes
        self.subfolder_checkboxes = {}
        self.create_subfolder_checkboxes()

    def update_feature_flags(self):
        feature_flag_name = self.feature_flag_name_entry.get()
        feature_flag_value = self.feature_flag_value_entry.get()
        
        if not feature_flag_name or not feature_flag_value:
            messagebox.showinfo("Info", "Please enter Feature Flag Name and Value.")
            return

        selected_subfolders = [subfolder for subfolder, var in self.subfolder_checkboxes.items() if var.get() == "1"]
        if not selected_subfolders:
            messagebox.showinfo("Info", "Please select at least one subfolder.")
            return
        
        # Create a processing message window
        processing_window = tk.Toplevel(self.root)
        processing_window.title("Processing")

        processing_label = tk.Label(processing_window, text="Updating feature flags. Please wait...")
        processing_label.pack(padx=20, pady=20)

        processing_window.update()  # Update the window to force it to appear

        
        error_messages = []  # List to store error messages
        success_messages = []

        repo = self.github.get_repo(self.repository)

        # Get the SHA of the base branch
        base_branch = repo.get_branch(self.base)
        base_branch_sha = base_branch.commit.sha

        # Get the contents of the "vbms-configuration" folder from the base branch
        base_contents = repo.get_contents("vbms-configuration", ref=self.base)

        while base_contents:
            file_content = base_contents.pop(0)
            if file_content.type == "dir":
                subfolder = file_content.name
                branch_name = f"{re.sub('[^a-zA-Z0-9-_]', '_', self.branchPrepend)}_{re.sub('[^a-zA-Z0-9-_]', '_', subfolder)}"
                # Check if the branch already exists
                if self.branch_exists(repo, branch_name):
                    error_messages.append(f"Error updating feature flag for {subfolder} - the branch {branch_name} already exists. Please change the branch prepend in the configuration or remove the branch in Github")
                elif subfolder in selected_subfolders:
                    try:
                        subfolder_path = f"vbms-configuration/{subfolder}/property_overrides/vbms_p2.properties"
                        file = repo.get_contents(subfolder_path, ref=self.base)

                        # Create the branch using the base branch SHA as the reference
                        repo.create_git_ref(f"refs/heads/{branch_name}", base_branch_sha)
                        try:
                            App.update_file(subfolder, repo, feature_flag_name, feature_flag_value, base_branch_sha, branch_name, error_messages, success_messages)
                        except Exception as e:
                            error_messages.append(f"else, Error updating feature flag for {subfolder}: {e}")
                    except Exception as e:
                        error_messages.append(f"Error creating branch {branch_name}: {e}")
                    try:
                        # Create the pull request
                        self.pr_title = f"Feature flag update for {subfolder}"
                        pull_request = self.create_pull_request(branch_name, subfolder)
                        success_messages.append(f"Pull request created successfully! URL: {pull_request.html_url}")
                    except Exception as e:
                        error_messages.append(f"Error creating pull request for {subfolder}: {e}")

        processing_window.destroy()

        # Display success and error messages at the end
        if success_messages:
            success_message = "\n".join(success_messages)
            messagebox.showinfo("Success", f"\n{success_message}")
        if error_messages:
            print(error_messages)
            error_message = "\n".join(error_messages)
            messagebox.showerror("Error", f"Encountered the following errors:\n{error_message}")

    def create_subfolder_checkboxes(self):
        g = Github(self.token)
        repo = g.get_repo(self.repository)
        base_contents = repo.get_contents("vbms-configuration", ref=self.base)

        row_index = 8  # Starting row index for checkboxes

        for file_content in base_contents:
            if file_content.type == "dir":
                subfolder = file_content.name
                subfolder_path = f"vbms-configuration/{subfolder}/property_overrides/vbms_p2.properties"
                
                try:
                    repo.get_contents(subfolder_path, ref=self.base)  # Check if the file exists
                    var = tk.StringVar(value="0")
                    checkbox = ttk.Checkbutton(self.pr_tab, text=subfolder, variable=var)
                    checkbox.grid(row=row_index, column=0, columnspan=2, sticky="w")
                    self.subfolder_checkboxes[subfolder] = var
                    row_index += 1
                except Exception:
                    # The vbms_p2.properties file doesn't exist, skip this subfolder
                    pass

        ttk.Separator(self.pr_tab, orient="horizontal").grid(row=row_index, column=0, columnspan=2, sticky="ew", pady=10)


    @staticmethod
    def read_config():
        config = configparser.ConfigParser()
        config.read('config.ini')
        github_config = config['Github']

        username = github_config.get('username')
        token = github_config.get('token')
        repository = github_config.get('repository')
        title = github_config.get('title')
        branchPrepend = github_config.get("branchPrepend")
        body = github_config.get('body')
        head = github_config.get('head')
        base = github_config.get('base')

        return username, token, repository, title, branchPrepend, body, head, base

    @staticmethod
    def write_config(username, token, repository, title, body, head, base):
        config = configparser.ConfigParser()
        config['Github'] = {
            'username': username,
            'token': token,
            'repository': repository,
            'title': title,
            'body': body,
            'head': head,
            'base': base
        }

        with open('config.ini', 'w') as configfile:
            config.write(configfile)

    def update_config(self):
        self.username = self.username_entry.get()
        self.token = self.token_entry.get()
        self.repository = self.repository_entry.get()
        self.title = self.title_entry.get()
        self.body = self.body_entry.get('1.0', 'end-1c')
        self.head = self.head_entry.get()
        self.base = self.base_entry.get()
        self.branchPrepend = self.branchPrepend.get()

        self.write_config(self.username, self.token, self.repository, self.title, self.body, self.head, self.base, self.branchPrepend)
        messagebox.showinfo("Configuration updated successfully!")

    def create_pull_request(self, branch_name, env):
        repo = self.github.get_repo(self.repository)
        return repo.create_pull(title=self.title + " " + env, body=self.body + " for " + env, head=branch_name, base=self.base)

    @staticmethod
    def branch_exists(repo, branch_name):
        try:
            repo.get_branch(branch_name)
            return True
        except:
            return False
        
    @staticmethod
    def update_file(subfolder, repo, feature_flag_name, feature_flag_value, base_branch_sha, branch_name, error_messages, success_messages):
        subfolder_path = f"vbms-configuration/{subfolder}/property_overrides/vbms_p2.properties"
        try:
            file = repo.get_contents(subfolder_path, ref=base_branch_sha)
            existing_content = file.decoded_content.decode()

            # Search for the feature flag in the existing content
            pattern = re.compile(rf"^{feature_flag_name}\s*=\s*.*$", re.MULTILINE)
            if pattern.search(existing_content):
                # Update the existing feature flag value
                new_content = pattern.sub(f"{feature_flag_name}={feature_flag_value}", existing_content)
            else:
                # Add the new feature flag
                new_content = f"{existing_content.strip()}\n{feature_flag_name}={feature_flag_value}"

            # Create the file update in the branch
            repo.update_file(file.path, f"feature flag change in {subfolder}", new_content, file.sha, branch=branch_name)
            success_messages.append(f"Feature flag updated for {subfolder}")
        except Exception as e:
            error_messages.append(f"Error updating feature flag for {subfolder}. Does vbms_p2.properties exist in {subfolder}?: {e}")

    def run(self):
        self.root.mainloop()

root = tk.Tk()
app = App(root)
app.run()