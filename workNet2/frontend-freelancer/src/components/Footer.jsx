import { Link } from 'react-router-dom';

const Footer = () => {
  return (
    <footer className="bg-gray-800 text-white mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          <div>
            <h3 className="text-lg font-bold mb-4">WorkNet Freelancer</h3>
            <p className="text-gray-400 text-sm">
              Grow your freelance business and connect with clients worldwide.
            </p>
          </div>
          <div>
            <h4 className="text-md font-semibold mb-4">For Freelancers</h4>
            <ul className="space-y-2 text-sm text-gray-400">
              <li>
                <Link to="/gigs" className="hover:text-white">
                  Manage Gigs
                </Link>
              </li>
              <li>
                <Link to="/messages" className="hover:text-white">
                  Messages
                </Link>
              </li>
              <li>
                <Link to="/" className="hover:text-white">
                  Dashboard
                </Link>
              </li>
            </ul>
          </div>
          <div>
            <h4 className="text-md font-semibold mb-4">Resources</h4>
            <ul className="space-y-2 text-sm text-gray-400">
              <li>
                <a href="#" className="hover:text-white">
                  Help Center
                </a>
              </li>
              <li>
                <a href="#" className="hover:text-white">
                  Freelancer Guide
                </a>
              </li>
              <li>
                <a href="#" className="hover:text-white">
                  Tips & Tricks
                </a>
              </li>
            </ul>
          </div>
          <div>
            <h4 className="text-md font-semibold mb-4">Support</h4>
            <ul className="space-y-2 text-sm text-gray-400">
              <li>
                <a href="#" className="hover:text-white">
                  Contact Support
                </a>
              </li>
              <li>
                <a href="#" className="hover:text-white">
                  FAQ
                </a>
              </li>
              <li>
                <a href="#" className="hover:text-white">
                  Privacy Policy
                </a>
              </li>
            </ul>
          </div>
        </div>
        <div className="border-t border-gray-700 mt-8 pt-8 text-center text-sm text-gray-400">
          <p>&copy; {new Date().getFullYear()} WorkNet Freelancer. All rights reserved.</p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;

