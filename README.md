# Dataset: missing conditional paths

## Missing conditional paths

*Missing conditional paths* are one of the most occurring class of defects found in software projects.
Missing conditional paths (also called missing conditions, neglected or missing cases) are a particular class of defects stemming from the absence of a particular piece of code, usually guarded by a condition.
The defect is thus caused by an incomplete set of behaviors rather than an erroneous one.
Evidences suggest that the missing cases are often omitted from specification and requirements, and correspond to unusual conditions or obscure combinations which are not considered by the developer.
This could explain why missing conditional paths are a class of defects particularly difficult to
detect by both manual and automated software testing approaches.

Studying versions of programs in software repositories provide relevant examples on how programmers address defects in programs.
We looked for methods in which a conditional paths was added in a commit: we thus focused on commit adding if statements without modifying the rest of the method.

## Extraction process

To identify added conditional paths in methods, we analyzed commits to isolate modified methods verifying the following constraints:
- the modified method must exists before and after the commit (i.e., the commit does not create nor delete the method)
-  no code must be deleted in the method by the commit
-  the added lines must be consecutive (a single fragment is added)
-  the added fragment must correspond to an *if* block


When studying changes made on source code, it is common to document these changes in the form of "code change diff", i.e., pairs of code snapshots representing the code on which the changes will be applied (before the commit) and the code on which the changes have been applied (after the commit).
For each method in which a conditional path is added, we thus gather the two versions of the modified method.
To facilitate further analysis of the added conditional paths, we also isolate the added code fragment and stored it in a third file.

## Repository

The repository has the following structure:

```
./
  extract.py
  config.json
  dataset/
    fragments/
    methods_before/
    methods_after/
    dataset.csv
```

The script *extract.py* implements the extraction process.

The configuration file *config.json* defines what projects to mine and where to stored the extracted data.
Each project to be mined is identified by its *url* (e.g., https://github.com/public-apis/public-apis) and the name of the *branch* in which the commits should be analyzed (e.g., *master*).
The extraction produced four different outputs, the configuration file thus expects four paths: a path to the directory storing the methods before the commit (*directory\_before*), a path to the directory storing the methods after the commit (*directory\_after*), a path to the directory storing the fragments (*directory\_fragments*) and a path to the csv file (*output\_csv*).
Hereafter an example of such configuration file:

```
  "directory_before": "./dataset/methods_before/",
  "directory_after": "./dataset/methods_after/",
  "directory_fragments": "./dataset/fragments/",
  "output_csv": "./dataset/dataset.csv",
  "projects": [
    {
      "url": "https://github.com/public-apis/public-apis",
      "branch": "master"
    }
  ]
}
```

Running *extract.py* with this configuration file will analyze the commits of one project, and store the extracted data into the directory *dataset/*.

## Dataset

We used the advanced search feature of GitHub to select repositories selected in Python.
In total, 1 393 projects were retrieved (trending projects, with the most stars and with the most forks).
This list of projects is provided in the file *list_projects.txt*.
We extracted a total of 78 000 methods in which a conditional path was added by a developer.

The dataset can be downloaded here: https://figshare.com/s/0609e9ee3f110d73c296
