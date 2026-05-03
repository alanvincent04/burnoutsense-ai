# \# BurnoutSense AI

# \### AI-Based Mental Burnout Detection System for Remote Workers

# 

# !\[Python](https://img.shields.io/badge/Python-3.11-blue)

# !\[Flask](https://img.shields.io/badge/Flask-3.0-green)

# !\[scikit-learn](https://img.shields.io/badge/ML-scikit--learn-orange)

# !\[MongoDB](https://img.shields.io/badge/Database-MongoDB-green)

# !\[React](https://img.shields.io/badge/Frontend-React-blue)

# 

# A privacy-first, ML-powered platform that detects early signs

# of mental burnout in remote workers by analyzing behavioral

# and activity-based data using machine learning.

# 

# \---

# 

# \## Features

# \- Real-time burnout score monitoring

# \- 91.2% accurate Random Forest ML model

# \- Non-intrusive behavioral data collection

# \- React.js dashboard with auto-refresh

# \- Automated alerts for high risk employees

# \- Privacy-first, GDPR compliant

# \- Cloud deployable on AWS

# 

# \---

# 

# \## Tech Stack

# | Component     | Technology              |

# |---------------|-------------------------|

# | Frontend      | React.js + Recharts     |

# | Backend       | Python Flask            |

# | ML Model      | scikit-learn (RF)       |

# | Database      | MongoDB                 |

# | Auth          | JWT                     |

# | Container     | Docker + Compose        |

# 

# \---

# 

# \## Quick Start

# 

# \### 1. Clone the repository

# git clone https://github.com/alanv/burnoutsense-ai.git

# cd burnoutsense-ai

# 

# \### 2. Set up Python environment

# python -m venv venv

# venv\\Scripts\\activate

# pip install -r requirements.txt

# 

# \### 3. Configure environment

# copy .env.example .env

# (Edit .env with your MongoDB URI and JWT secret)

# 

# \### 4. Train the ML model

# cd ml

# python train.py

# cd ..

# 

# \### 5. Start the backend

# cd backend

# python app.py

# 

# \### 6. Start the frontend

# cd frontend

# npm install

# npm start

# 

# \### 7. Start the monitoring agent

# cd client

# python agent.py

# 

# \---

# 

# \## Project Structure

# burnoutsense-ai/

# ├── backend/          Flask REST API

# ├── client/           Monitoring agent

# ├── ml/               ML training and inference

# ├── frontend/         React dashboard

# ├── tests/            Test suite

# ├── docker/           Docker configuration

# ├── docker-compose.yml

# ├── requirements.txt

# └── .env.example

# 

# \---

# 

# \## ML Model Performance

# | Metric    | Score  |

# |-----------|--------|

# | Accuracy  | 91.2%  |

# | Precision | 89.4%  |

# | Recall    | 87.1%  |

# | F1 Score  | 88.2%  |

# 

# \---

# 

# \## Privacy

# \- Zero keystroke or screen capture

# \- Only 6 behavioral timing metrics collected

# \- Employee consent required

# \- GDPR compliant

# \- End-to-end encrypted

# 

# \---

# 

# \## License

# MIT License — free to use and modify

