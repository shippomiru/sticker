import React from 'react';
import { Download, Tags, Search } from 'lucide-react';
import { useTranslation } from 'react-i18next';

export function About() {
  const { t } = useTranslation();

  return (
    <main className="flex-grow max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
      <div className="space-y-16">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-medium text-gray-900">About ImageAI</h1>
        </div>

        {/* Mission */}
        <section>
          <h2 className="text-xl font-medium text-gray-900 mb-4">Our Mission</h2>
          <p className="text-gray-600 leading-relaxed text-lg">
            ImageAI is a free image resource platform dedicated to providing high-quality image assets for designers, developers, and creators. Our platform offers a curated collection of professional images that are free to use in both personal and commercial projects.
          </p>
        </section>

        {/* How to Use */}
        <section>
          <h2 className="text-xl font-medium text-gray-900 mb-8">How to Use</h2>
          <div className="space-y-8">
            <div className="flex items-start gap-5">
              <Search className="h-6 w-6 text-blue-600 stroke-[1.75] mt-1" />
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">Search Images</h3>
                <p className="text-lg text-gray-600 leading-relaxed">
                  Use the search bar at the top to find images instantly. Our search supports both English and Chinese, searching through image titles and descriptions.
                </p>
              </div>
            </div>

            <div className="flex items-start gap-5">
              <Tags className="h-6 w-6 text-blue-600 stroke-[1.75] mt-1" />
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">Filter by Tags</h3>
                <p className="text-lg text-gray-600 leading-relaxed">
                  Use tags to quickly filter specific types of images. You can combine multiple tags to find exactly what you need.
                </p>
              </div>
            </div>

            <div className="flex items-start gap-5">
              <Download className="h-6 w-6 text-blue-600 stroke-[1.75] mt-1" />
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">Download Images</h3>
                <p className="text-lg text-gray-600 leading-relaxed">
                  Each image comes in multiple formats: original, transparent sticker, and white background sticker. Click on any image to access the download options.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* License */}
        <section>
          <h2 className="text-xl font-medium text-gray-900 mb-4">Image License</h2>
          <p className="text-lg text-gray-600 leading-relaxed mb-6">
            All images on ImageAI are free to use for both personal and commercial purposes. Our license terms are simple:
          </p>
          <ul className="text-lg text-gray-600 space-y-3">
            <li className="flex items-center gap-3">
              <span className="w-1.5 h-1.5 bg-gray-400 rounded-full"></span>
              Free to use, no payment required
            </li>
            <li className="flex items-center gap-3">
              <span className="w-1.5 h-1.5 bg-gray-400 rounded-full"></span>
              Suitable for both commercial and non-commercial use
            </li>
            <li className="flex items-center gap-3">
              <span className="w-1.5 h-1.5 bg-gray-400 rounded-full"></span>
              Attribution to ImageAI is appreciated but not required
            </li>
            <li className="flex items-center gap-3">
              <span className="w-1.5 h-1.5 bg-gray-400 rounded-full"></span>
              Reselling unmodified images is not permitted
            </li>
          </ul>
        </section>

        {/* Contact */}
        <section>
          <h2 className="text-xl font-medium text-gray-900 mb-4">Contact Us</h2>
          <p className="text-lg text-gray-600 leading-relaxed mb-6">
            Have questions, suggestions, or interested in collaboration? We'd love to hear from you:
          </p>
          <div className="space-y-2 text-lg text-gray-600">
            <p>Email: contact@imageai.com</p>
            <p>WeChat: ImageAI_Support</p>
          </div>
        </section>
      </div>
    </main>
  );
}

export default About;