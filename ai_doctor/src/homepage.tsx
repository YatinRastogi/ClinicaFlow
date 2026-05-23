import { useState, useEffect } from 'react';
import {
  Brain,
  Stethoscope,
  Shield,
  Clock,
  CheckCircle,
  TrendingUp,
  Users,
  FileText,
  ArrowRight,
  Play,
  Star,
  Award,
  Activity,
  Lock,
  Globe,
  BarChart3,
  MessageCircle,
  Phone,
  Mail,
  Menu,
  X
} from 'lucide-react';

const DiagnosticHomepage = () => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [currentTestimonial, setCurrentTestimonial] = useState(0);

  const testimonials = [
    {
      name: "Dr. Sarah Chen",
      role: "Emergency Medicine Physician",
      hospital: "Johns Hopkins Hospital",
      content: "This AI diagnostic tool has revolutionized our triage process. We've reduced diagnostic time by 40% while maintaining 97% accuracy.",
      rating: 5
    },
    {
      name: "Dr. Michael Rodriguez",
      role: "Internal Medicine Specialist",
      hospital: "Mayo Clinic",
      content: "The explainable AI features give me confidence in the recommendations. It's like having a brilliant resident available 24/7.",
      rating: 5
    },
    {
      name: "Dr. Emily Watson",
      role: "Chief Medical Officer",
      hospital: "Cleveland Clinic",
      content: "Implementation was seamless, and the red-flag detection has already helped us catch several critical cases early.",
      rating: 5
    }
  ];

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentTestimonial((prev) => (prev + 1) % testimonials.length);
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  const stats = [
    { value: 'Multi-LLM', label: 'Specialist Routing', icon: TrendingUp },
    { value: '<2 min', label: 'Avg. Analysis Time', icon: Clock },
    { value: '3+', label: 'Specialist Pathways', icon: Users },
    { value: '24/7', label: 'Availability', icon: Globe }
  ];

  const features = [
    {
      icon: Brain,
      title: 'AI-Powered Analysis',
      description: 'Advanced machine learning algorithms analyze patient data across multiple dimensions for accurate diagnosis.',
      color: 'text-blue-500'
    },
    {
      icon: Shield,
      title: 'Critical Alert System',
      description: 'Immediate red-flag detection for life-threatening conditions like sepsis, stroke, and cardiac events.',
      color: 'text-red-500'
    },
    {
      icon: FileText,
      title: 'Comprehensive Reports',
      description: 'Detailed diagnostic reports with evidence-based reasoning and confidence scores for clinical decision-making.',
      color: 'text-green-500'
    },
    {
      icon: Lock,
      title: 'HIPAA Compliant',
      description: 'Enterprise-grade security with end-to-end encryption and full compliance with healthcare regulations.',
      color: 'text-purple-500'
    },
    {
      icon: Activity,
      title: 'Real-Time Processing',
      description: 'Instant analysis of patient data with live updates and collaborative workflow integration.',
      color: 'text-orange-500'
    },
    {
      icon: BarChart3,
      title: 'Analytics Dashboard',
      description: 'Comprehensive insights and performance metrics to optimize healthcare delivery and outcomes.',
      color: 'text-indigo-500'
    }
  ];

  const workflow = [
    {
      step: '01',
      title: 'Data Input',
      description: 'Patient enters symptoms, vitals, and uploads medical records through our intuitive interface.',
      icon: Users
    },
    {
      step: '02',
      title: 'AI Analysis',
      description: 'Multiple specialized agents process the data using advanced medical AI and clinical decision rules.',
      icon: Brain
    },
    {
      step: '03',
      title: 'Risk Assessment',
      description: 'System identifies critical conditions and stratifies risk levels with immediate alerts for emergencies.',
      icon: Shield
    },
    {
      step: '04',
      title: 'Clinical Report',
      description: 'Comprehensive diagnostic report generated with ranked diagnoses and explainable AI reasoning.',
      icon: FileText
    }
  ];

  return (
    <div className="min-h-screen bg-white">
      {/* Navigation */}
      <nav className="bg-white shadow-sm border-b sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <div className="flex-shrink-0 flex items-center">
                <div className="bg-gradient-to-r from-blue-600 to-indigo-700 p-2 rounded-lg mr-3">
                  <Stethoscope className="text-white" size={24} />
                </div>
                <span className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-indigo-700 bg-clip-text text-transparent">
                  ClinicaFlow
                </span>
              </div>
            </div>

            {/* Desktop Menu */}
            <div className="hidden md:block">
              <div className="ml-10 flex items-center space-x-8">
                <a href="#features" className="text-gray-700 hover:text-blue-600 font-medium">Features</a>
                <a href="#how-it-works" className="text-gray-700 hover:text-blue-600 font-medium">How It Works</a>
                <a href="#testimonials" className="text-gray-700 hover:text-blue-600 font-medium">Testimonials</a>
                <a href="#contact" className="text-gray-700 hover:text-blue-600 font-medium">Contact</a>
                <button className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 font-medium">
                  Get Started
                </button>
              </div>
            </div>

            {/* Mobile menu button */}
            <div className="md:hidden">
              <button
                onClick={() => setIsMenuOpen(!isMenuOpen)}
                className="text-gray-700 hover:text-blue-600"
              >
                {isMenuOpen ? <X size={24} /> : <Menu size={24} />}
              </button>
            </div>
          </div>

          {/* Mobile Menu */}
          {isMenuOpen && (
            <div className="md:hidden border-t">
              <div className="px-2 pt-2 pb-3 space-y-1">
                <a href="#features" className="block px-3 py-2 text-gray-700 hover:text-blue-600 font-medium">Features</a>
                <a href="#how-it-works" className="block px-3 py-2 text-gray-700 hover:text-blue-600 font-medium">How It Works</a>
                <a href="#testimonials" className="block px-3 py-2 text-gray-700 hover:text-blue-600 font-medium">Testimonials</a>
                <a href="#contact" className="block px-3 py-2 text-gray-700 hover:text-blue-600 font-medium">Contact</a>
                <button className="w-full text-left bg-blue-600 text-white px-3 py-2 rounded-lg hover:bg-blue-700 font-medium mt-2">
                  Get Started
                </button>
              </div>
            </div>
          )}
        </div>
      </nav>

      {/* Hero Section */}
      <section className="bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 py-20">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div>
              <div className="inline-flex items-center bg-blue-100 text-blue-800 px-4 py-2 rounded-full text-sm font-medium mb-6">
                <Award className="mr-2" size={16} />
                AI-Powered Clinical Decision Support
              </div>
              <h1 className="text-5xl lg:text-6xl font-bold text-gray-900 mb-6 leading-tight">
                <span className="bg-gradient-to-r from-blue-600 to-indigo-700 bg-clip-text text-transparent block">
                  ClinicaFlow
                </span>
                AI-Powered Clinical Diagnostics
              </h1>
              <p className="text-xl text-gray-600 mb-8 leading-relaxed">
                An AI diagnostic assistant that synthesizes patient data, symptoms, and medical records to generate preliminary clinical assessments — helping healthcare professionals gather information faster and more systematically. Always reviewed by a qualified clinician.
              </p>
              <div className="flex flex-col sm:flex-row gap-4 mb-12">
                <button className="bg-gradient-to-r from-blue-600 to-indigo-700 text-white px-8 py-4 rounded-lg text-lg font-semibold hover:from-blue-700 hover:to-indigo-800 transform hover:scale-105 transition-all duration-200 shadow-lg flex items-center justify-center">
                  Start Diagnosis
                  <ArrowRight className="ml-2" size={20} />
                </button>
                <button className="border-2 border-gray-300 text-gray-700 px-8 py-4 rounded-lg text-lg font-semibold hover:border-blue-600 hover:text-blue-600 transition-all duration-200 flex items-center justify-center">
                  <Play className="mr-2" size={20} />
                  Watch Demo
                </button>
              </div>

              {/* Stats */}
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
                {stats.map((stat, index) => (
                  <div key={index} className="text-center">
                    <div className="flex justify-center mb-2">
                      <stat.icon className="text-blue-600" size={24} />
                    </div>
                    <div className="text-2xl font-bold text-gray-900">{stat.value}</div>
                    <div className="text-sm text-gray-600">{stat.label}</div>
                  </div>
                ))}
              </div>
            </div>

            <div className="relative">
              <div className="bg-white rounded-2xl shadow-2xl p-8 transform rotate-2 hover:rotate-0 transition-transform duration-300">
                <div className="bg-gradient-to-r from-red-500 to-orange-500 text-white p-4 rounded-lg mb-6">
                  <div className="flex items-center">
                    <Shield className="mr-3" size={24} />
                    <div>
                      <h3 className="font-semibold">Critical Alert</h3>
                      <p className="text-sm opacity-90">Sepsis Risk Detected</p>
                    </div>
                  </div>
                </div>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-gray-600">Primary Diagnosis:</span>
                    <span className="font-semibold">Bacterial Sepsis</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-gray-600">Confidence:</span>
                    <div className="flex items-center">
                      <div className="w-20 bg-gray-200 rounded-full h-2 mr-2">
                        <div className="bg-red-500 h-2 rounded-full" style={{width: '87%'}}></div>
                      </div>
                      <span className="font-semibold">87%</span>
                    </div>
                  </div>
                  <div className="pt-4 border-t">
                    <p className="text-sm text-gray-600">
                      <strong>Key Evidence:</strong> High fever (102.3°F), elevated WBC, tachycardia
                    </p>
                  </div>
                </div>
              </div>
              <div className="absolute -top-4 -right-4 bg-green-500 text-white p-3 rounded-full shadow-lg">
                <CheckCircle size={24} />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-gray-900 mb-4">
              Powerful Features for
              <span className="text-blue-600"> Modern Healthcare</span>
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Our AI diagnostic platform combines cutting-edge technology with clinical expertise to deliver accurate, fast, and explainable medical diagnoses.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature, index) => (
              <div key={index} className="bg-gray-50 p-8 rounded-xl hover:bg-white hover:shadow-lg transition-all duration-300 border border-transparent hover:border-gray-200">
                <div className={`${feature.color} mb-4`}>
                  <feature.icon size={48} />
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-3">{feature.title}</h3>
                <p className="text-gray-600 leading-relaxed">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section id="how-it-works" className="py-20 bg-gradient-to-br from-gray-50 to-blue-50">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-gray-900 mb-4">
              How It Works
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Our streamlined process ensures accurate diagnostics through intelligent AI analysis and clinical validation.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {workflow.map((item, index) => (
              <div key={index} className="relative">
                <div className="bg-white p-6 rounded-xl shadow-sm hover:shadow-md transition-shadow duration-300">
                  <div className="bg-gradient-to-r from-blue-600 to-indigo-700 text-white w-16 h-16 rounded-full flex items-center justify-center mb-6 mx-auto">
                    <item.icon size={24} />
                  </div>
                  <div className="text-center">
                    <div className="text-sm font-semibold text-blue-600 mb-2">STEP {item.step}</div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-3">{item.title}</h3>
                    <p className="text-gray-600 text-sm leading-relaxed">{item.description}</p>
                  </div>
                </div>
                {index < workflow.length - 1 && (
                  <div className="hidden lg:block absolute top-8 left-full w-8 h-0.5 bg-gradient-to-r from-blue-300 to-transparent transform translate-y-8"></div>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Testimonials */}
      <section id="testimonials" className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-gray-900 mb-4">
              Trusted by Healthcare Professionals
            </h2>
            <p className="text-xl text-gray-600">
              See what medical experts are saying about our AI diagnostic platform
            </p>
          </div>

          <div className="bg-gradient-to-r from-blue-50 to-indigo-50 p-8 rounded-2xl">
            <div className="text-center max-w-4xl mx-auto">
              <div className="flex justify-center mb-6">
                {[...Array(testimonials[currentTestimonial].rating)].map((_, i) => (
                  <Star key={i} className="text-yellow-400 fill-current" size={24} />
                ))}
              </div>
              <blockquote className="text-2xl text-gray-800 font-medium mb-8 leading-relaxed">
                "{testimonials[currentTestimonial].content}"
              </blockquote>
              <div className="flex items-center justify-center">
                <div className="text-center">
                  <div className="font-semibold text-gray-900 text-lg">
                    {testimonials[currentTestimonial].name}
                  </div>
                  <div className="text-blue-600 font-medium">
                    {testimonials[currentTestimonial].role}
                  </div>
                  <div className="text-gray-600 text-sm">
                    {testimonials[currentTestimonial].hospital}
                  </div>
                </div>
              </div>
            </div>

            {/* Testimonial indicators */}
            <div className="flex justify-center mt-8 space-x-2">
              {testimonials.map((_, index) => (
                <button
                  key={index}
                  onClick={() => setCurrentTestimonial(index)}
                  className={`w-3 h-3 rounded-full transition-colors duration-200 ${
                    index === currentTestimonial ? 'bg-blue-600' : 'bg-gray-300'
                  }`}
                />
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-gradient-to-r from-blue-600 to-indigo-700">
        <div className="max-w-7xl mx-auto px-6 text-center">
          <h2 className="text-4xl font-bold text-white mb-4">
            Ready to Transform Your Practice?
          </h2>
          <p className="text-xl text-blue-100 mb-8 max-w-3xl mx-auto">
            Join hundreds of healthcare facilities already using our AI diagnostic platform to improve patient outcomes and streamline clinical workflows.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <button className="bg-white text-blue-600 px-8 py-4 rounded-lg text-lg font-semibold hover:bg-gray-100 transform hover:scale-105 transition-all duration-200 shadow-lg">
              Request Demo
            </button>
            <button className="border-2 border-white text-white px-8 py-4 rounded-lg text-lg font-semibold hover:bg-white hover:text-blue-600 transition-all duration-200">
              Contact Sales
            </button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer id="contact" className="bg-gray-900 text-white py-16">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            <div className="col-span-1 md:col-span-2">
              <div className="flex items-center mb-6">
                <div className="bg-gradient-to-r from-blue-600 to-indigo-700 p-2 rounded-lg mr-3">
                  <Stethoscope className="text-white" size={24} />
                </div>
                <span className="text-2xl font-bold">ClinicaFlow</span>
              </div>
              <p className="text-gray-300 mb-6 max-w-md">
                Revolutionizing healthcare with AI-powered diagnostic tools that enhance clinical decision-making and improve patient outcomes.
              </p>
              <div className="flex space-x-4">
                <button className="bg-gray-800 p-3 rounded-lg hover:bg-gray-700 transition-colors">
                  <MessageCircle size={20} />
                </button>
                <button className="bg-gray-800 p-3 rounded-lg hover:bg-gray-700 transition-colors">
                  <Mail size={20} />
                </button>
                <button className="bg-gray-800 p-3 rounded-lg hover:bg-gray-700 transition-colors">
                  <Phone size={20} />
                </button>
              </div>
            </div>

            <div>
              <h3 className="text-lg font-semibold mb-4">Platform</h3>
              <ul className="space-y-2 text-gray-300">
                <li><a href="#" className="hover:text-white transition-colors">Features</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Pricing</a></li>
                <li><a href="#" className="hover:text-white transition-colors">API Docs</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Integration</a></li>
              </ul>
            </div>

            <div>
              <h3 className="text-lg font-semibold mb-4">Support</h3>
              <ul className="space-y-2 text-gray-300">
                <li><a href="#" className="hover:text-white transition-colors">Help Center</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Contact Us</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Privacy Policy</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Terms of Service</a></li>
              </ul>
            </div>
          </div>

          <div className="border-t border-gray-800 mt-12 pt-8 text-center text-gray-400">
            <p>&copy; 2025 ClinicaFlow. All rights reserved. For research and clinical decision support only — not a substitute for professional medical advice.</p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default DiagnosticHomepage;