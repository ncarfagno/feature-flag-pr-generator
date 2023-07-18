import os
import configparser
from github import Github
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import re
import time

def read_config():
    config = configparser.ConfigParser()
    config.read('config.ini')
    github_config = config['Github']

    username = github_config.get('username')
    token = github_config.get('token')
    repository = github_config.get('repository')
    title = github_config.get('title')
    body = github_config.get('body')
    head = github_config.get('head')
    base = github_config.get('base')

    return username, token, repository, title, body, head, base

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

def create_pull_request(username, token, repository, title, body, head, base):
    g = Github(token)
    repo = g.get_repo(repository)
    return repo.create_pull(title=title, body=body, head=head, base=base)

def update_config():
    username = username_entry.get()
    token = token_entry.get()
    repository = repository_entry.get()
    title = title_entry.get()
    body = body_entry.get('1.0', 'end-1c')
    head = head_entry.get()
    base = base_entry.get()

    write_config(username, token, repository, title, body, head, base)
    messagebox.showinfo("Configuration updated successfully!")

def branch_exists(repo, branch_name):
    try:
        repo.get_branch(branch_name)
        return True
    except:
        return False
    
def update_file(subfolder, repo, feature_flag_name, feature_flag_value, branch_name,base_branch_sha, error_messages, success_messages):
    # Use forward slashes in the path
    subfolder_path = f"vbms-configuration/{subfolder}/property_overrides/vbms_p2.properties"
    try:
        file = repo.get_contents(subfolder_path, ref=base)
        existing_content = file.decoded_content.decode()
        new_content = f"{existing_content.strip()}\n{feature_flag_name}={feature_flag_value}"
        # Create the file update in the branch
        repo.update_file(file.path, f"feature flag change in {subfolder}", new_content, file.sha, branch=branch_name)
        success_messages.append(f"Feature flag updated for {subfolder}")
    except Exception as e:
        error_messages.append(f"Error updating feature flag for {subfolder}. Does vbms_p2.properties exist in {subfolder}?: {e}")

def update_feature_flags(feature_flag_name, feature_flag_value):
    error_messages = []  # List to store error messages
    success_messages = []
    username, token, repository, title, body, head, base = read_config()

    g = Github(token)
    repo = g.get_repo(repository)

    # Get the SHA of the base branch
    base_branch = repo.get_branch(base)
    base_branch_sha = base_branch.commit.sha

    # Get the contents of the "vbms-configuration" folder from the base branch
    base_contents = repo.get_contents("vbms-configuration", ref=base)

    while base_contents:
        file_content = base_contents.pop(0)
        if file_content.type == "dir":
            subfolder = file_content.name
            branch_name = f"{re.sub('[^a-zA-Z0-9-_]', '_', title)}_{re.sub('[^a-zA-Z0-9-_]', '_', subfolder)}"

            # Check if the branch already exists
            if branch_exists(repo, branch_name):
                try:
                    update_file(subfolder, repo, feature_flag_name, feature_flag_value, branch_name,base_branch_sha, error_messages, success_messages)
                except Exception as e:
                    error_messages.append(f"Error updating feature flag for {subfolder}: {e}")
            else:
                try:
                    subfolder_path = f"vbms-configuration/{subfolder}/property_overrides/vbms_p2.properties"
                    file = repo.get_contents(subfolder_path, ref=base)

                    # Create the branch using the base branch SHA as the reference
                    repo.create_git_ref(f"refs/heads/{branch_name}", base_branch_sha)
                    try:
                        update_file(subfolder, repo, feature_flag_name, feature_flag_value, branch_name,base_branch_sha, error_messages, success_messages)
                    except Exception as e:
                        error_messages.append(f"else, Error updating feature flag for {subfolder}: {e}")
                except Exception as e:
                    error_messages.append(f"Error creating branch {branch_name}: {e}")
            pr_title = f"Feature flag update for {subfolder}"
            try:
                # Create the pull request
                pull_request = create_pull_request(username, token, repository, pr_title, body, branch_name, base)
                success_messages.append(f"Pull request created successfully! URL: {pull_request.html_url}")
            except Exception as e:
                error_messages.append(f"Error creating pull request for {subfolder}: {e}")
    if success_messages:
        success_message = "\n".join(success_messages)
        messagebox.showinfo("Success", f"\n{success_message}")
    if error_messages:
        error_message = "\n".join(error_messages)
        messagebox.showerror("Error", f"Encountered the following errors:\n{error_message}")


# Create the main application window
root = tk.Tk()
root.title("GitHub Pull Request App")

# Create the Notebook widget to hold multiple tabs
notebook = ttk.Notebook(root)
notebook.pack(fill=tk.BOTH, expand=True)

# Update Configuration Tab
update_tab = ttk.Frame(notebook)
notebook.add(update_tab, text="Update Configuration")

# Read GitHub configuration from the configuration file
username, token, repository, title, body, head, base = read_config()

# Create labels and entry fields for GitHub configuration
ttk.Label(update_tab, text="GitHub Username:").grid(row=0, column=0)
username_entry = ttk.Entry(update_tab)
username_entry.insert(0, username)  # Set the default value
username_entry.grid(row=0, column=1)

ttk.Label(update_tab, text="GitHub Token:").grid(row=1, column=0)
token_entry = ttk.Entry(update_tab)
token_entry.insert(0, token)  # Set the default value
token_entry.grid(row=1, column=1)

ttk.Label(update_tab, text="Repository:").grid(row=2, column=0)
repository_entry = ttk.Entry(update_tab)
repository_entry.insert(0, repository)  # Set the default value
repository_entry.grid(row=2, column=1)

ttk.Label(update_tab, text="Pull Request Title:").grid(row=3, column=0)
title_entry = ttk.Entry(update_tab)
title_entry.insert(0, title)  # Set the default value
title_entry.grid(row=3, column=1)

ttk.Label(update_tab, text="Pull Request Body:").grid(row=4, column=0)
body_entry = tk.Text(update_tab, width=30, height=5)
body_entry.insert('1.0', body)  # Set the default value
body_entry.grid(row=4, column=1)

ttk.Label(update_tab, text="Branch with Changes:").grid(row=5, column=0)
head_entry = ttk.Entry(update_tab)
head_entry.insert(0, head)  # Set the default value
head_entry.grid(row=5, column=1)

ttk.Label(update_tab, text="Base Branch:").grid(row=6, column=0)
base_entry = ttk.Entry(update_tab)
base_entry.insert(0, base)  # Set the default value
base_entry.grid(row=6, column=1)

# Create button for updating configuration
update_config_button = ttk.Button(update_tab, text="Update Configuration", command=update_config)
update_config_button.grid(row=7, column=0, columnspan=2, pady=10)

# Create Pull Request Tab
pr_tab = ttk.Frame(notebook)
notebook.add(pr_tab, text="Create Pull Request")

# Entry fields for Feature Flag Name and Feature Flag Value
ttk.Label(pr_tab, text="Feature Flag Name:").grid(row=0, column=0)
feature_flag_name_entry = ttk.Entry(pr_tab)
feature_flag_name_entry.grid(row=0, column=1)

ttk.Label(pr_tab, text="Feature Flag Value:").grid(row=1, column=0)
feature_flag_value_entry = ttk.Entry(pr_tab)
feature_flag_value_entry.grid(row=1, column=1)

# Create button for updating feature flags
update_flags_button = ttk.Button(pr_tab, text="Update Feature Flags", command=lambda: update_feature_flags(feature_flag_name_entry.get(), feature_flag_value_entry.get()))
update_flags_button.grid(row=2, column=0, columnspan=2, pady=10)

# Start the main event loop
root.mainloop()