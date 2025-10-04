# LLM-Tester Enhanced - Relocatable Architecture

**Advanced LLM testing and parameter optimization platform with visualization and persistent data management**

## 🚀 Overview

LLM-Tester Enhanced is a comprehensive platform for testing Large Language Models with advanced parameter optimization, multidimensional visualization, and research-grade analytics. This relocatable architecture integrates seamlessly with MasterMenu while supporting device relocation through symlinks and maintaining full data persistence.

## 📁 Directory Structure

```
llm-tester/
├── 📄 README.md                    # This documentation
├── 📄 app.yaml                     # MasterMenu tool manifest
├── 🔧 run.sh                       # Smart launcher with environment setup
├── 📁 src/                         # Source code
│   └── 📄 LLM_Tester_Enhanced.py   # Main application
├── 📁 lib/                         # Shared libraries
│   └── 📄 path_manager.py          # Path management & symlinks
├── 📁 config/                      # Configuration files
│   └── 📄 config.yaml              # Application settings
├── 📁 data/                        # Persistent data storage
│   ├── 📁 external/                # External data (symlinked)
│   ├── 📁 models/                  # Model storage
│   └── 📁 exports/                 # Exported results
├── 📁 db/                          # Database storage
│   └── 📄 llm_tester.db            # Main database
├── 📁 results/                     # Results and analysis
│   ├── 📁 optimization/            # Optimization results
│   ├── 📁 testing/                 # Test results
│   ├── 📁 visualizations/          # Graphs and charts
│   └── 📁 exports/                 # Result exports
├── 📁 logs/                        # Application logs
├── 📁 tools/                       # Additional tools
└── 📁 .venv/                       # Virtual environment (auto-created)
```

## 🛠️ Installation & Setup

### Automatic Setup

The application automatically handles all setup when first launched:

1. **Virtual Environment**: Creates isolated Python environment
2. **Dependencies**: Installs all required packages automatically
3. **Path Management**: Configures relocatable paths with symlink support
4. **Data Migration**: Detects and links to existing desktop data
5. **Validation**: Verifies complete installation

### Manual Validation

```bash
# Navigate to application directory
cd /home/herb/Desktop/MasterMenu/apps/llm-tester

# Validate installation (dry run)
./run.sh --validate-only

# Force reinstall dependencies
./run.sh --reinstall

# Clean and recreate environment
./run.sh --clean
```

## 🎯 Key Features

### 1. Parameter Optimization Lab
- **Exhaustive Search**: Systematic parameter space exploration
- **Convergence Algorithm**: Iterates until finding optimal settings
- **Real-time Progress**: Live monitoring of optimization runs
- **Statistical Validation**: Ensures consistent, repeatable results
- **100% Accuracy Target**: Optimizes for perfect accuracy with minimum time

### 2. Multidimensional Visualization
- **3D Performance Landscape**: Surface plots of parameter interactions
- **Optimization Path**: Journey analysis showing convergence
- **Parameter Heatmap**: Correlation analysis between parameters
- **Parallel Coordinates**: Multi-dimensional parameter relationships

### 3. Persistent Data Management
- **Relocatable Architecture**: Device relocation through symlinks
- **Automatic Backups**: Built-in backup and restore system
- **Data Migration**: Seamless integration with existing data
- **Storage Analytics**: Monitor storage usage and optimization

### 4. MasterMenu Integration
- **Native Integration**: Full MasterMenu framework support
- **CLI Wrapper**: Command-line interface for automation
- **Environment Isolation**: Independent of other tools
- **Smart Launcher**: Handles all environment setup automatically

## 🔧 Configuration

### Main Configuration (`config/config.yaml`)

```yaml
application:
  name: "LLM-Tester Enhanced"
  version: "2.0.0"

# Model configurations
models:
  default_provider: "ollama"
  timeout: 300
  max_retries: 3
  available:
    - id: "phi3:3.8b"
      name: "Phi-3 Mini (3.8B)"
      context_limit: 4096
    - id: "phi3:14b"
      name: "Phi-3 Medium (14B)"
      context_limit: 8192

# Testing parameters
testing:
  default_parameters:
    temperature: 0.7
    num_ctx: 2048
    num_predict: 512
    repeat_penalty: 1.1
    top_k: 25
    top_p: 0.9
```

## 📊 Usage Examples

### Running Parameter Optimization

1. **Launch Application**:
   ```bash
   ./run.sh
   ```

2. **Navigate to Optimization Lab**:
   - Open the "🔬 Optimization Lab" tab
   - Enter your test prompt
   - Select model and parameters
   - Click "Start Optimization"

3. **Monitor Progress**:
   - Real-time progress updates
   - Current configuration display
   - Accuracy and timing metrics
   - Convergence analysis

4. **View Results**:
   - Automatic visualization generation
   - 4 different graph types
   - Export capabilities
   - Historical tracking

### Command Line Interface

```bash
# Run with specific parameters
./run.sh --debug

# Validate installation only
./run.sh --validate-only

# Show help
./run.sh --help
```

## 🔄 Data Persistence & Relocation

### Automatic Symlink Creation

The application automatically detects existing LLM-Tester data and creates symlinks for seamless data access.

### Device Relocation

When moving to a new device:

1. **Install MasterMenu** on new device
2. **Copy** the `apps/llm-tester` directory
3. **Run** `./run.sh --validate-only`
4. **Update** external symlinks as needed

## 📈 Optimization Parameters

### Supported Parameters

| Parameter | Range | Description |
|-----------|-------|-------------|
| `temperature` | 0.1 - 1.0 | Response randomness |
| `num_ctx` | 1024 - 8192 | Context window size |
| `num_predict` | 256 - 2048 | Maximum response length |
| `repeat_penalty` | 1.0 - 1.3 | Repetition control |
| `top_k` | 10 - 50 | Token selection diversity |
| `top_p` | 0.8 - 1.0 | Nucleus sampling |

## 🎨 Visualization Types

1. **Performance Landscape** (3D Surface)
2. **Optimization Path** (Journey Analysis)
3. **Parameter Heatmap** (Correlation Matrix)
4. **Parallel Coordinates** (Multi-dimensional View)

## 🛠️ Troubleshooting

### Common Issues

```bash
# Clean reinstall
./run.sh --clean
./run.sh --reinstall

# Validate paths
./run.sh --validate-only

# Check logs
tail -f logs/app.log
```

## 🔗 Integration Points

### MasterMenu Integration
- **Tool Manifest**: `app.yaml` defines tool metadata
- **CLI Wrapper**: Automatic generation of command-line interface
- **Environment Isolation**: Independent operation from other tools
- **Data Persistence**: Shared data storage across sessions

### External Tools
- **Ollama Integration**: Local model serving
- **Database Storage**: SQLite for persistent data
- **Export Formats**: JSON, CSV, XLSX support
- **Visualization**: Matplotlib/Seaborn integration

---

**🎯 Success Metrics**: 100% accuracy with consistent, repeatable optimization results in minimum time.
