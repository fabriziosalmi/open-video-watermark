# Contributing to Open Video Watermark

Thank you for your interest in contributing to Open Video Watermark! This document provides guidelines and information for contributors.

## 🚀 Getting Started

### Prerequisites

- Python 3.12+
- Docker and Docker Compose
- Git
- Basic knowledge of Flask, OpenCV, and video processing

### Development Setup

1. **Fork and clone the repository**:
```bash
git clone https://github.com/YOUR_USERNAME/open-video-watermark.git
cd open-video-watermark
```

2. **Set up development environment**:
```bash
make setup
make install
```

3. **Run tests to ensure everything works**:
```bash
make test
```

## 📝 Development Guidelines

### Code Style

- Follow PEP 8 for Python code
- Use Black for code formatting: `make format`
- Run linting: `make lint`
- Add type hints where appropriate
- Write docstrings for all functions and classes

### Commit Messages

Use conventional commit format:
```
feat: add new watermarking algorithm
fix: resolve memory leak in video processing
docs: update installation instructions
test: add unit tests for DCT watermarking
refactor: optimize video frame processing
```

### Branch Naming

- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation updates
- `test/description` - Test additions/improvements

## 🧪 Testing

### Running Tests

```bash
# Run all tests
make test

# Run with coverage
pytest --cov=watermark tests/

# Run specific test file
pytest tests/test_watermark.py -v
```

### Writing Tests

- Add tests for all new functionality
- Place tests in the `tests/` directory
- Use descriptive test names
- Include both positive and negative test cases
- Test edge cases and error conditions

## 📚 Documentation

### Code Documentation

- Add docstrings to all functions and classes
- Include parameter descriptions and return values
- Provide usage examples for complex functions

### README Updates

- Update README.md for new features
- Include configuration examples
- Add troubleshooting information

## 🐛 Bug Reports

When reporting bugs, please include:

1. **Description**: Clear description of the issue
2. **Steps to Reproduce**: Detailed steps to reproduce the bug
3. **Expected Behavior**: What should happen
4. **Actual Behavior**: What actually happens
5. **Environment**: OS, Python version, Docker version
6. **Logs**: Relevant error messages or logs

## 💡 Feature Requests

For feature requests, please provide:

1. **Use Case**: Why is this feature needed?
2. **Description**: Detailed description of the feature
3. **Implementation Ideas**: Any thoughts on implementation
4. **Alternatives**: Alternative solutions considered

## 🔄 Pull Request Process

1. **Create a feature branch** from `main`
2. **Make your changes** following the guidelines above
3. **Add tests** for new functionality
4. **Update documentation** as needed
5. **Run the test suite** and ensure all tests pass
6. **Submit a pull request** with a clear description

### Pull Request Checklist

- [ ] Code follows style guidelines
- [ ] Tests added for new functionality
- [ ] All tests pass
- [ ] Documentation updated
- [ ] No breaking changes (or clearly documented)
- [ ] Commit messages follow conventional format

## 🏗️ Architecture Overview

### Core Components

- **app.py**: Main Flask application and routing
- **watermark/**: Core watermarking algorithms
- **static/**: Frontend assets (CSS, JavaScript)
- **templates/**: HTML templates

### Key Technologies

- **Backend**: Flask, SocketIO, OpenCV, NumPy
- **Frontend**: Vanilla JavaScript, WebSockets
- **Containerization**: Docker, Docker Compose
- **Proxy**: Nginx (production)

## 🔐 Security

### Security Guidelines

- Validate all user inputs
- Use secure file handling practices
- Implement proper error handling
- Don't expose sensitive information in logs
- Follow OWASP security guidelines

### Reporting Security Issues

Please report security vulnerabilities privately by emailing the maintainers. Do not create public issues for security vulnerabilities.

## 📞 Getting Help

- **GitHub Issues**: For bugs and feature requests
- **GitHub Discussions**: For questions and general discussion
- **Code Review**: Submit PRs for feedback

## 🙏 Recognition

Contributors will be recognized in:
- GitHub contributors list
- Release notes for significant contributions
- README acknowledgments section

Thank you for contributing to Open Video Watermark! 🎬
